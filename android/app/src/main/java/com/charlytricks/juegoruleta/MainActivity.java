package com.charlytricks.juegoruleta;

import android.annotation.SuppressLint;
import android.content.Context;
import android.content.SharedPreferences;
import android.media.AudioManager;
import android.os.Build;
import android.os.Bundle;
import android.speech.tts.TextToSpeech;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.Manifest;
import android.content.pm.PackageManager;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import java.util.Locale;

/**
 * 🎡 JuegoRuleta — Ruleta didáctica de enfermería
 * WebView que carga el juego (index.html) desde el server del dueño.
 * Bridge nativo:
 *   - getApiUrl(): devuelve la URL base de la API
 *   - getDeviceModel(): modelo del celular
 *   - hablar(texto): TTS nativo para leer situaciones/feedback
 */
public class MainActivity extends AppCompatActivity {

    public static final String API_URL = "http://157.250.202.243:8090";
    private WebView webView;
    private TextToSpeech tts;
    private boolean ttsListo = false;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Volumen de medios para el audio de las tarjetas
        setVolumeControlStream(AudioManager.STREAM_MUSIC);

        // TTS nativo (lectura de las situaciones)
        tts = new TextToSpeech(this, status -> {
            if (status == TextToSpeech.SUCCESS) {
                int res = tts.setLanguage(new Locale("es", "AR"));
                ttsListo = res != TextToSpeech.LANG_MISSING_DATA && res != TextToSpeech.LANG_NOT_SUPPORTED;
            }
        });

        // Permiso de micrófono (respuesta por voz)
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
                != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.RECORD_AUDIO}, 100);
        }

        webView = findViewById(R.id.webView);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setAllowFileAccess(true);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onPermissionRequest(android.webkit.PermissionRequest request) {
                runOnUiThread(() -> request.grant(request.getResources()));
            }
        });

        webView.setWebViewClient(new WebViewClient());
        webView.addJavascriptInterface(new Bridge(), "AndroidBridge");

        // Cargar el juego
        webView.loadUrl(API_URL + "/");
    }

    /** Bridge nativo expuesto al JS del juego. */
    private class Bridge {
        @JavascriptInterface
        public String getApiUrl() {
            return API_URL;
        }

        @JavascriptInterface
        public String getDeviceModel() {
            return Build.MODEL;
        }

        @JavascriptInterface
        public void hablar(String texto) {
            if (ttsListo && texto != null && !texto.isEmpty()) {
                runOnUiThread(() -> {
                    tts.stop();
                    tts.speak(texto, TextToSpeech.QUEUE_FLUSH, null, "ruleta");
                });
            }
        }

        @JavascriptInterface
        public void detenerVoz() {
            if (tts != null) {
                runOnUiThread(() -> tts.stop());
            }
        }
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {
        if (tts != null) {
            tts.stop();
            tts.shutdown();
        }
        super.onDestroy();
    }
}
