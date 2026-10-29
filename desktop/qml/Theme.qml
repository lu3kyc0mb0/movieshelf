pragma Singleton
import QtQuick

QtObject {
    readonly property bool dark: shelf.state.preferences.theme === "dark"
    readonly property bool motion: shelf.state.preferences.animations
    readonly property string language: shelf.state.preferences.language
    readonly property color background: paletteColor("background", dark ? "#17181c" : "#fafafc")
    readonly property color sidebar: paletteColor("sidebar", dark ? "#1f2026" : "#f1f2f5")
    readonly property color surface: paletteColor("surface", dark ? "#25262e" : "#ffffff")
    readonly property color elevated: paletteColor("elevated", dark ? "#30313b" : "#eff0f4")
    readonly property color hover: paletteColor("hover", dark ? "#353743" : "#e7e9ef")
    readonly property color line: paletteColor("line", dark ? "#353640" : "#e4e6ed")
    readonly property color text: paletteColor("text", dark ? "#f3f3f7" : "#242531")
    readonly property color secondary: paletteColor("secondary", dark ? "#a3a5b5" : "#747785")
    readonly property color accent: paletteColor("accent", dark ? "#409cff" : "#007aff")
    readonly property color selected: paletteColor("selected", dark ? "#253b56" : "#e1edfc")
    readonly property color danger: paletteColor("danger", dark ? "#ff858c" : "#cf3548")
    readonly property color gold: paletteColor("gold", dark ? "#f2cd7d" : "#a77821")
    readonly property color accentText: paletteColor("onAccent", "#ffffff")
    readonly property real textScale: shelf.state.preferences.text_scale || 1
    function px(size) { return Math.round(size * textScale) }
    function paletteColor(key, fallback) { return shelf.state.preferences.colors[key] || fallback }
    readonly property int duration: motion ? 180 : 0
    function tr(key) {
        let currentLanguage = language
        return shelf.trText(key)
    }
}
