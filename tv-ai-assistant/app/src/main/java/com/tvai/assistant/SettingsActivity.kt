package com.tvai.assistant

import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity

class SettingsActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)
        val prefs = getSharedPreferences("tvai_prefs", MODE_PRIVATE)
        val etKey = findViewById<EditText>(R.id.etApiKey)
        val btnSave = findViewById<Button>(R.id.btnSave)
        val txtStatus = findViewById<TextView>(R.id.txtStatus)
        etKey.setText(prefs.getString("gemini_key", "") ?: "")
        btnSave.setOnClickListener {
            val key = etKey.text.toString().trim()
            if (key.isEmpty()) {
                Toast.makeText(this, "Key khali nahi ho sakti", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            prefs.edit().putString("gemini_key", key).apply()
            txtStatus.text = "Key save ho chuka hai"
            Toast.makeText(this, "Save ho gaya", Toast.LENGTH_SHORT).show()
        }
    }
}
