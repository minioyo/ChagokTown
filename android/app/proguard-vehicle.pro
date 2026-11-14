# Pleos Vehicle SDK parses platform replies with Gson TypeToken and reflection, but its bundled rules keep only the API
# implementations. Without these, R8 strips the generic signatures and every capability/odometer read fails in release.
-keep class ai.pleos.playground.** { *; }
-keepattributes Signature

# Gson's own rules for TypeToken under R8 full mode.
-keep,allowobfuscation,allowshrinking class com.google.gson.reflect.TypeToken
-keep,allowobfuscation,allowshrinking class * extends com.google.gson.reflect.TypeToken
