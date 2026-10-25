package com.tvai.assistant

import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException

class ApiService(private val apiKey: String) {
    private val client = OkHttpClient()
    private val JSON = "application/json; charset=utf-8".toMediaType()

    fun askGemini(question: String, callback: (String) -> Unit) {
        val url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=$apiKey"
        val parts = JSONObject().put("text", question)
        val content = JSONObject().put("parts", JSONArray().put(parts))
        val contents = JSONArray().put(content)
        val bodyJson = JSONObject().put("contents", contents)
        val body = bodyJson.toString().toRequestBody(JSON)

        val request = Request.Builder()
            .url(url)
            .post(body)
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                callback("Network error: ${e.message}")
            }

            override fun onResponse(call: Call, response: Response) {
                response.use {
                    val responseBody = it.body?.string() ?: ""
                    if (!it.isSuccessful) {
                        callback("API error ${it.code}: $responseBody")
                        return@use
                    }
                    try {
                        val json = JSONObject(responseBody)
                        if (json.has("error")) {
                            val err = json.getJSONObject("error")
                            val msg = err.optString("message", "Unknown error")
                            callback("Error: $msg")
                            return@use
                        }
                        val candidates = json.getJSONArray("candidates")
                        val cand = candidates.getJSONObject(0)
                        val contentObj = cand.getJSONObject("content")
                        val partsArr = contentObj.getJSONArray("parts")
                        val text = partsArr.getJSONObject(0).getString("text")
                        callback(text)
                    } catch (e: Exception) {
                        callback("Parse error: ${e.message}")
                    }
                }
            }
        })
    }
}
