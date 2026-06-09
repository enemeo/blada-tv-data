package com.example.vladatv

import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale

object DataProviderPartidos {

    suspend fun cargarPartidos(): List<PartidoItem> {
        return withContext(Dispatchers.IO) {
            try {
                val url =
                    "https://raw.githubusercontent.com/enemeo/blada-tv-data/main/partidos.json?nocache=${System.currentTimeMillis()}"

                val jsonString = URL(url).readText()
                println("PARTIDOS JSON: $jsonString")

                val listType = object : TypeToken<List<PartidoItem>>() {}.type

                val partidos: List<PartidoItem> =
                    Gson().fromJson(jsonString, listType)

                partidos.filter { partido ->
                    partido.estado.equals("En progreso", true) ||
                            !partidoYaPaso(partido.fecha, partido.hora, partido.estado)
                }

            } catch (e: Exception) {
                println("ERROR PARTIDOS: ${e.message}")
                emptyList()
            }
        }
    }

    private fun partidoYaPaso(fecha: String, hora: String, estado: String): Boolean {
        return try {
            if (
                estado.equals("Finalizado", true) ||
                estado.equals("FT", true) ||
                estado.equals("AET", true) ||
                estado.equals("PEN", true)
            ) {
                return true
            }

            if (hora.isBlank()) return false

            val actualYear =
                Calendar.getInstance().get(Calendar.YEAR)

            val formatos = listOf(
                SimpleDateFormat("dd/MM h:mm a", Locale.US),
                SimpleDateFormat("dd/MM h:mm a", Locale("es", "PE")),
                SimpleDateFormat("dd/MM H:mm", Locale.US),
                SimpleDateFormat("dd/MM HH:mm", Locale.US)
            )

            var calPartido: Calendar? = null

            for (formato in formatos) {
                try {
                    val fechaParseada = formato.parse("$fecha $hora")
                    if (fechaParseada != null) {
                        calPartido = Calendar.getInstance()
                        calPartido.time = fechaParseada
                        calPartido.set(Calendar.YEAR, actualYear)
                        break
                    }
                } catch (_: Exception) {
                }
            }

            if (calPartido == null) {
                return false
            }

            // Desaparece 2 horas después de la hora de inicio
            calPartido.add(Calendar.HOUR_OF_DAY, 2)

            val ahora = Calendar.getInstance()

            ahora.after(calPartido)

        } catch (e: Exception) {
            false
        }
    }
}
