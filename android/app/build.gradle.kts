import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.compose.compiler)
    alias(libs.plugins.ksp)
    alias(libs.plugins.room)
}

// Release signing is read from android/keystore.properties (kept out of git). Without it, release builds are unsigned.
val releaseSigning = rootProject.file("keystore.properties").takeIf { it.exists() }?.let { file ->
    Properties().apply { file.inputStream().use { load(it) } }
}

android {
    namespace = "com.chagoktown"
    compileSdk = 36
    buildToolsVersion = "36.0.0"
    // Compile-time stubs for CarUxRestrictionsManager. Only vehicle code references them; the device provides the library.
    useLibrary("android.car")

    defaultConfig {
        applicationId = "com.chagoktown"
        minSdk = 28
        targetSdk = 36
        versionCode = 9
        versionName = "0.8.1-balance"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        // Filament ships native code per CPU. arm64 is the expected car CPU (not yet verified on Pleos); x86_64 runs the emulator.
        ndk { abiFilters += listOf("arm64-v8a", "x86_64") }
    }

    signingConfigs {
        if (releaseSigning != null) {
            create("release") {
                storeFile = rootProject.file(releaseSigning.getProperty("storeFile"))
                storePassword = releaseSigning.getProperty("storePassword")
                keyAlias = releaseSigning.getProperty("keyAlias")
                keyPassword = releaseSigning.getProperty("keyPassword")
            }
        }
    }

    buildTypes {
        release {
            signingConfig = signingConfigs.findByName("release")
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"))
        }
    }

    flavorDimensions += "environment"
    productFlavors {
        create("demo") {
            dimension = "environment"
            applicationIdSuffix = ".demo"
        }
        create("vehicle") {
            dimension = "environment"
            proguardFile("proguard-vehicle.pro")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    buildFeatures {
        compose = true
    }
}

kotlin {
    jvmToolchain(17)
}

room {
    schemaDirectory("$projectDir/schemas")
}

dependencies {
    implementation(project(":game"))
    implementation(platform(libs.compose.bom))
    implementation(libs.compose.ui)
    implementation(libs.compose.foundation)
    implementation(libs.compose.material3)
    implementation(libs.activity.compose)
    implementation(libs.lifecycle.runtime.compose)
    implementation(libs.lifecycle.viewmodel.compose)
    implementation(libs.room.runtime)
    implementation(libs.coroutines.android)
    implementation(libs.sceneview)
    ksp(libs.room.compiler)
    "vehicleImplementation"(libs.pleos.vehicle)

    testImplementation(libs.junit)
    androidTestImplementation(platform(libs.compose.bom))
    androidTestImplementation(libs.compose.ui.test)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.runner)
    debugImplementation(libs.compose.test.manifest)
}
