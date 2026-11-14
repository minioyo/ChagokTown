package com.chagoktown.data

import android.content.res.AssetManager
import com.chagoktown.game.ConstructionCatalog
import com.chagoktown.game.PlotDefinition
import org.json.JSONObject

data class PlotScene(val id: String, val models: List<String>, val x: Float, val y: Float, val z: Float,
    val width: Float, val depth: Float, val padOffsetX: Float, val padOffsetZ: Float, val rotationY: Float) {
    init { require(models.size == 3) }
    fun modelPath(level: Int): String {
        require(level in 1..3)
        return models[level - 1]
    }
}

data class TownCamera(val target: List<Float>, val offset: List<Float>, val verticalSpan: Float)

data class TownRoad(val node: String, val plots: Set<String>) {
    fun isVisible(buildings: Map<String, Int>): Boolean = plots.any { (buildings[it] ?: 0) > 0 }
}

data class TownLayout(val catalog: ConstructionCatalog, val plots: List<PlotScene>, val environmentModel: String, val camera: TownCamera,
    val roads: List<TownRoad>)

fun loadTownLayout(assets: AssetManager): TownLayout {
    val data = JSONObject(assets.open("layout/season1_town.json").bufferedReader().use { it.readText() })
    val plots = data.getJSONArray("plots")
    val definitions = (0 until plots.length()).map { i ->
        val p = plots.getJSONObject(i)
        val costs = p.getJSONArray("costs")
        PlotDefinition(p.getString("id"), p.getString("name"), (0 until costs.length()).map(costs::getInt))
    }
    val scene = (0 until plots.length()).map { i ->
        val p = plots.getJSONObject(i)
        val models = p.getJSONArray("models")
        PlotScene(p.getString("id"), (0 until models.length()).map(models::getString), p.getDouble("x").toFloat(), p.getDouble("y").toFloat(), p.getDouble("z").toFloat(),
            p.getDouble("width").toFloat(), p.getDouble("depth").toFloat(), p.getDouble("padOffsetX").toFloat(), p.getDouble("padOffsetZ").toFloat(), p.getDouble("rotationY").toFloat())
    }
    val camera = data.getJSONObject("camera")
    fun vector(key: String) = camera.getJSONArray(key).let { array ->
        require(array.length() == 3)
        (0..2).map { array.getDouble(it).toFloat() }
    }
    val roads = data.getJSONArray("roads").let { array -> (0 until array.length()).map { i ->
        val road = array.getJSONObject(i)
        val owners = road.getJSONArray("plots")
        TownRoad(road.getString("node"), (0 until owners.length()).map(owners::getString).toSet()).also {
            require(it.plots.isNotEmpty() && it.plots.all { id -> definitions.any { p -> p.id == id } })
        }
    } }
    require(roads.map { it.node }.distinct().size == roads.size)
    return TownLayout(ConstructionCatalog(definitions), scene, data.getString("environmentModel"),
        TownCamera(vector("target"), vector("offset"), camera.getDouble("verticalSpan").toFloat()), roads)
}
