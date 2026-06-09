import fs from "fs/promises";
import { chromium } from "playwright";

const ARCHIVO_FUENTES = "fuentes_canales.json";
const ARCHIVO_CANALES = "canales_m3u8.json";
const ARCHIVO_PARTIDOS = "partidos.json";

function normalizarUrl(url) {
  if (!url) return "";
  return String(url)
    .trim()
    .replace(/\\u0026/g, "&")
    .replace(/&amp;/g, "&");
}

function esM3U8(url) {
  return typeof url === "string" && url.toLowerCase().includes(".m3u8");
}

async function leerJson(ruta, valorDefault) {
  try {
    const texto = await fs.readFile(ruta, "utf8");
    if (!texto.trim()) return valorDefault;
    return JSON.parse(texto);
  } catch {
    return valorDefault;
  }
}

async function guardarJson(ruta, data) {
  await fs.writeFile(ruta, JSON.stringify(data, null, 2) + "\n", "utf8");
}

function obtenerUrlFuente(config) {
  if (typeof config === "string") return config;
  if (config && typeof config === "object") {
    return config.url || config.pagina || "";
  }
  return "";
}

function obtenerEspera(config) {
  if (config && typeof config === "object" && config.esperarMs) {
    return Number(config.esperarMs);
  }
  return 18000;
}

async function validarM3U8(url, request) {
  try {
    const respuesta = await request.get(url, {
      timeout: 20000,
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
        Accept: "*/*",
        Referer: "https://tvporinternet2.com/"
      }
    });

    if (!respuesta.ok()) return false;

    const texto = await respuesta.text();

    return (
      texto.includes("#EXTM3U") ||
      texto.includes("#EXT-X-STREAM-INF") ||
      texto.includes("#EXTINF")
    );
  } catch {
    return false;
  }
}

async function buscarM3U8DeCanal(browser, canal, config) {
  const urlPagina = obtenerUrlFuente(config);
  const esperarMs = obtenerEspera(config);

  if (!urlPagina || urlPagina.includes("TU-PAGINA-AUTORIZADA")) {
    console.log(`⏭️ ${canal}: fuente no configurada`);
    return null;
  }

  console.log("========================================");
  console.log(`🔎 Buscando ${canal}`);
  console.log(`🌐 Fuente: ${urlPagina}`);

  const context = await browser.newContext({
    userAgent:
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
      "Chrome/124.0.0.0 Safari/537.36",
    viewport: { width: 1366, height: 768 },
    ignoreHTTPSErrors: true
  });

  const page = await context.newPage();
  const encontrados = new Set();

  const capturar = (url) => {
    const limpio = normalizarUrl(url);
    if (esM3U8(limpio)) {
      console.log(`📡 Detectado ${canal}: ${limpio}`);
      encontrados.add(limpio);
    }
  };

  page.on("request", (request) => capturar(request.url()));
  page.on("response", (response) => capturar(response.url()));
  page.on("framenavigated", (frame) => capturar(frame.url()));

  try {
    await page.goto(urlPagina, {
      waitUntil: "domcontentloaded",
      timeout: 60000
    });

    await page.waitForTimeout(5000);

    // Algunos reproductores cargan el M3U8 solo después de tocar Play.
    try {
      await page.mouse.click(680, 380);
      await page.waitForTimeout(5000);
    } catch {}

    // Intenta detectar botones de play comunes.
    try {
      const posiblesBotones = [
        "button",
        ".play",
        ".vjs-big-play-button",
        ".jwplayer",
        "video"
      ];

      for (const selector of posiblesBotones) {
        const elemento = await page.$(selector);
        if (elemento) {
          await elemento.click({ timeout: 3000 }).catch(() => {});
          await page.waitForTimeout(3000);
        }
      }
    } catch {}

    // Revisa HTML principal.
    try {
      const html = await page.content();
      const regex = /https?:\/\/[^"'\\\s<>]+?\.m3u8[^"'\\\s<>]*/gi;
      const matches = html.match(regex) || [];
      for (const link of matches) capturar(link);
    } catch {}

    // Revisa iframes.
    for (const frame of page.frames()) {
      try {
        capturar(frame.url());

        const htmlFrame = await frame.content();
        const regex = /https?:\/\/[^"'\\\s<>]+?\.m3u8[^"'\\\s<>]*/gi;
        const matches = htmlFrame.match(regex) || [];
        for (const link of matches) capturar(link);
      } catch {}
    }

    // Espera final para capturar peticiones tardías de hls.js.
    await page.waitForTimeout(esperarMs);
  } catch (error) {
    console.log(`❌ ${canal}: ${error.message}`);
  }

  const lista = Array.from(encontrados);
  console.log(`📺 ${canal}: encontrados ${lista.length} enlaces m3u8`);

  for (const link of lista) {
    const valido = await validarM3U8(link, context.request);

    if (valido) {
      console.log(`✅ ${canal}: M3U8 válido`);
      await context.close();
      return link;
    }
  }

  if (lista.length > 0) {
    console.log(`⚠️ ${canal}: usando el primer M3U8 detectado`);
    await context.close();
    return lista[0];
  }

  console.log(`❌ ${canal}: no se encontró M3U8`);
  await context.close();
  return null;
}

async function actualizarPartidos(canales) {
  const partidos = await leerJson(ARCHIVO_PARTIDOS, []);

  if (!Array.isArray(partidos)) {
    console.log("⚠️ partidos.json no es una lista");
    return;
  }

  let cambios = false;

  const actualizados = partidos.map((partido) => {
    const canal = partido.canal;

    if (canal && canales[canal]) {
      if (partido.videoUrl !== canales[canal]) {
        cambios = true;
        return {
          ...partido,
          videoUrl: canales[canal]
        };
      }
    }

    return partido;
  });

  if (cambios) {
    await guardarJson(ARCHIVO_PARTIDOS, actualizados);
    console.log("✅ partidos.json actualizado con nuevos M3U8");
  } else {
    console.log("ℹ️ partidos.json sin cambios");
  }
}

async function main() {
  const fuentes = await leerJson(ARCHIVO_FUENTES, {});
  const canalesActuales = await leerJson(ARCHIVO_CANALES, {});

  const browser = await chromium.launch({
    headless: true
  });

  const nuevosCanales = { ...canalesActuales };

  for (const [canal, config] of Object.entries(fuentes)) {
    const m3u8 = await buscarM3U8DeCanal(browser, canal, config);

    if (m3u8) {
      nuevosCanales[canal] = m3u8;
    } else if (!nuevosCanales[canal]) {
      nuevosCanales[canal] = "";
    }
  }

  await browser.close();

  await guardarJson(ARCHIVO_CANALES, nuevosCanales);
  await actualizarPartidos(nuevosCanales);

  console.log("✅ canales_m3u8.json actualizado");
  console.log(JSON.stringify(nuevosCanales, null, 2));
}

main().catch((error) => {
  console.error("ERROR GENERAL:", error);
  process.exit(1);
});
