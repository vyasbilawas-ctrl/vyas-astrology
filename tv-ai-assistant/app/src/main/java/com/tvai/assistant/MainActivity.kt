package com.tvai.assistant

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.SharedPreferences
import android.content.pm.PackageManager
import android.os.Bundle
import android.speech.RecognizerIntent
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {
    private lateinit var buttonSpeak: Button
    private lateinit var buttonSettings: Button
    private lateinit var resultView: TextView
    private lateinit var prefs: SharedPreferences
    private var apiService: ApiService? = null
    private val REQUEST_CODE_SPEECH = 101
    private val REQUEST_CODE_AUDIO = 102

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        buttonSpeak = findViewById(R.id.btnSpeak)
        buttonSettings = findViewById(R.id.btnSettings)
        resultView = findViewById(R.id.txtResult)
        prefs = getSharedPreferences("tvai_prefs", MODE_PRIVATE)
        initApiService()
        buttonSpeak.setOnClickListener { checkAudioPermissionAndSpeak() }
        buttonSettings.setOnClickListener {
            startActivity(Intent(this, SettingsActivity::class.java))
        }
    }

    override fun onResume() {
        super.onResume()
        initApiService()
    }

    private fun initApiService() {
        val apiKey = prefs.getString("gemini_key", "") ?: ""
        apiService = if (apiKey.isNotEmpty()) ApiService(apiKey) else null
        if (apiKey.isEmpty()) {
            resultView.text = "Gemini key nahi mila.\nSettings me key add karo, phir Bolo dabao."
        }
    }

    private fun checkAudioPermissionAndSpeak() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
            != PackageManager.PERMISSION_GRANTED
        ) {
            ActivityCompat.requestPermissions(
                this,
                arrayOf(Manifest.permission.RECORD_AUDIO),
                REQUEST_CODE_AUDIO
            )
            return
        }
        startSpeech()
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQUEST_CODE_AUDIO) {
            if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                startSpeech()
            } else {
                Toast.makeText(this, "Microphone permission chahiye", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun startSpeech() {
        val service = apiService
        if (service == null) {
            resultView.text = "Pehle Settings me Gemini API key set karo."
            return
        }
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
        intent.putExtra(
            RecognizerIntent.EXTRA_LANGUAGE_MODEL,
            RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
        )
        intent.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
        intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "Puchho...")
        try {
            startActivityForResult(intent, REQUEST_CODE_SPEECH)
        } catch (e: Exception) {
            resultView.text = "Error: ${e.message}"
        }
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQUEST_CODE_SPEECH) {
            if (resultCode == Activity.RESULT_OK) {
                val results = data?.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
                val spoken = results?.firstOrNull() ?: ""
                if (spoken.isEmpty()) {
                    resultView.text = "Kuch suna nahi gaya"
                    return
                }
                resultView.text = "Tum: $spoken\n\nSoch raha hu..."
                apiService?.askGemini(spoken) { response ->
                    runOnUiThread {
                        resultView.text = "Tum: $spoken\n\nAI: $response"
                    }
                }
            } else if (resultCode == Activity.RESULT_CANCELED) {
                resultView.text = "Speech cancel hua ya mic nahi mila."
            }
        }
    }
}
