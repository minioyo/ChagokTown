package com.chagoktown.ui.town

/** Seconds on a monotonic frame clock. No callbacks or persistent animation state. */
internal object BuildingMotion {
    const val BUILD_SECONDS = .76f
    const val UPGRADE_SECONDS = .56f
    const val SWAP_SECONDS = .14f

    private fun smooth(value: Float): Float = value.coerceIn(0f, 1f).let { it * it * (3f - 2f * it) }

    fun scale(seconds: Float, upgrade: Boolean): Float {
        if (upgrade && seconds < SWAP_SECONDS) return 1f - .12f * smooth(seconds / SWAP_SECONDS)
        val delay = if (upgrade) SWAP_SECONDS else .10f
        val duration = if (upgrade) UPGRADE_SECONDS else BUILD_SECONDS
        val t = ((seconds - delay) / (duration - delay)).coerceIn(0f, 1f)
        val start = if (upgrade) .88f else .08f
        return if (t < .78f) start + (1.025f - start) * smooth(t / .78f)
        else 1.025f - .025f * smooth((t - .78f) / .22f)
    }
}
