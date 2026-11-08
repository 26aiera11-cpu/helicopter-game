package com.helitrio.offlinetest;

import android.content.Context;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.view.Surface;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

/** Optional WebView fallback. Raw m/s² uses the game's existing gravity math. */
@CapacitorPlugin(name = "HeliMotion")
public class HeliMotionPlugin extends Plugin implements SensorEventListener {
    private SensorManager manager;
    private Sensor sensor;
    private boolean listening;
    @Override public void load() {
        manager = (SensorManager) getContext().getSystemService(Context.SENSOR_SERVICE);
        if (manager != null) {
            sensor = manager.getDefaultSensor(Sensor.TYPE_GRAVITY);
            if (sensor == null) sensor = manager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
        }
    }
    @PluginMethod public void start(PluginCall call) {
        getActivity().runOnUiThread(() -> {
            if (!listening && manager != null && sensor != null)
                listening = manager.registerListener(this, sensor, 20000);
            JSObject result = new JSObject();result.put("available", listening);call.resolve(result);
        });
    }
    private void stopSensor() {
        if (manager != null) manager.unregisterListener(this);
        listening = false;
    }
    @PluginMethod public void stop(PluginCall call) {
        getActivity().runOnUiThread(() -> {stopSensor();call.resolve();});
    }
    @Override protected void handleOnPause() {stopSensor();}
    @Override protected void handleOnDestroy() {stopSensor();}
    @Override public void onAccuracyChanged(Sensor sensor, int accuracy) {}
    @Override public void onSensorChanged(SensorEvent event) {
        if (!listening) return;
        int rotation = getActivity().getWindowManager().getDefaultDisplay().getRotation();
        int angle = rotation == Surface.ROTATION_90 ? 90 : rotation == Surface.ROTATION_180 ? 180 : rotation == Surface.ROTATION_270 ? 270 : 0;
        JSObject data = new JSObject();data.put("x", event.values[0]);data.put("y", event.values[1]);data.put("z", event.values[2]);data.put("rotation", angle);
        notifyListeners("gravity", data);
    }
}
