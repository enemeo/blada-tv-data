import fs from 'fs/promises';
import { chromium } from 'playwright';

const ARCHIVO_FUENTES = 'fuentes_canales.json';
const ARCHIVO_CANALES = 'canales_m3u8.json';
const ARCHIVO_PARTIDOS = 'partidos.json';

function normalizarUrl(url) {
  if (!url) return '';
  return String(url).trim().replace(/\\u0026/g, '&');
}

function esM3U8(url) {
  return typeof url === 'string' && url.includes('.m3u8');
}

async function leerJson(ruta, valorDefault) {
  try {
    const texto = await fs.readFile(ruta, 'utf8');
    return JSON.parse(texto);
  } catch {
    return valorDefault;
  }
}

async function guardarJson(ruta, data) {
  await fs.writeFile(ruta, JSON.stringify(data, null, 2) + '\n', 'utf8');
}

async function validarM3U8(url, request) {
  try {
    const respuesta = await request.get(url, {
      timeout: 15000,
      headers: {
        'User-Agent': 'Mozilla/5.0 BladaTV',
        'Accept': '*/*'
      }
    });

    if (!respuesta.ok()) return false;

    const texto = await respuesta.text();
    return texto.includes('#EXTM3U') || texto.includes('#EXT-X-STREAM-INF') || texto.includes('#EXTINF');
  } catch {
    return false;
  }
}

async function buscarM3U8DeCanal(browser, canal, config) {
  const urlPagina = typeof config === 'string' ? config : config.url;
  const esperarMs = typeof config === 'object' && config.esperarMs ? config.esperarMs : 10000;

  if (!urlPagina || urlPagina.includes('TU-PAGINA-AUTORIZADA')) {
    console.log(`⏭️  ${canal}: fuente no configurada`);
    return null;
  }

  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36',
    viewport: { width: 1366, height: 768 }
  });

  const page = await context.newPage();
  const encontrados = new Set();

  page.on('request', request => {
    const u = normalizarUrl(request.url());
    if (esM3U8(u)) encontrados.add(u);
  });

  page.on('response', response => {
    const u = normalizarUrl(response.url());
    if (esM3U8(u)) encontrados.add(u);
  });

  try {
    console.log(`🔎 Buscando ${canal}: ${urlPagina}`);
    await page.goto(urlPagina, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(esperarMs);

    const html = await page.content();
    const regex = /https?:[^"'\\\s]+?\.m3u8[^"'\\\s]*/gi;
    const matches = html.match(regex) || [];
    for (const m of matches) encontrados.add(normalizarUrl(m));

    const lista = Array.from(encontrados);
    console.log(`📺 ${canal}: encontrados ${lista.length} enlaces m3u8`);

    for (const link of lista) {
      const valido = await validarM3U8(link, context.request);
      if (valido) {
        console.log(`✅ ${canal}: ${link}`);
        await context.close();
        return link;
      }
    }

    if (lista.length > 0) {
      console.log(`⚠️  ${canal}: se encontró m3u8 pero no se pudo validar, usando el primero`);
      await context.close();
      return lista[0];
    }

    await context.close();
    return null;
  } catch (error) {
    console.log(`❌ ${canal}: ${error.message}`);
    await context.close();
    return null;
  }
}

async function actualizarPartidos(canales) {
  const partidos = await leerJson(ARCHIVO_PARTIDOS, []);

  const actualizados = partidos.map(partido => {
    const canal = partido.canal;
    if (canal && canales[canal]) {
      return {
        ...partido,
        videoUrl: canales[canal]
      };
    }
    return partido;
  });

  await guardarJson(ARCHIVO_PARTIDOS, actualizados);
}

async function main() {
  const fuentes = await leerJson(ARCHIVO_FUENTES, {});
  const canalesActuales = await leerJson(ARCHIVO_CANALES, {});

  const browser = await chromium.launch({ headless: true });
  const nuevosCanales = { ...canalesActuales };

  for (const [canal, config] of Object.entries(fuentes)) {
    const m3u8 = await buscarM3U8DeCanal(browser, canal, config);
    if (m3u8) nuevosCanales[canal] = m3u8;
  }

  await browser.close();

  await guardarJson(ARCHIVO_CANALES, nuevosCanales);
  await actualizarPartidos(nuevosCanales);

  console.log('✅ canales_m3u8.json y partidos.json actualizados');
}

main().catch(error => {
  console.error(error);
  process.exit(1);
});
