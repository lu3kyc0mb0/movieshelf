pragma Singleton
import QtQuick

QtObject {
    readonly property bool dark: shelf.state.preferences.theme === "dark"
    readonly property bool motion: shelf.state.preferences.animations
    readonly property string language: shelf.state.preferences.language
    readonly property color background: dark ? "#17181c" : "#fafafc"
    readonly property color sidebar: dark ? "#1f2026" : "#f1f2f5"
    readonly property color surface: dark ? "#25262e" : "#ffffff"
    readonly property color elevated: dark ? "#30313b" : "#eff0f4"
    readonly property color hover: dark ? "#353743" : "#e7e9ef"
    readonly property color line: dark ? "#353640" : "#e4e6ed"
    readonly property color text: dark ? "#f3f3f7" : "#242531"
    readonly property color secondary: dark ? "#a3a5b5" : "#747785"
    readonly property color accent: dark ? "#409cff" : "#007aff"
    readonly property color selected: dark ? "#253b56" : "#e1edfc"
    readonly property color danger: dark ? "#ff858c" : "#cf3548"
    readonly property color gold: dark ? "#f2cd7d" : "#a77821"
    readonly property int duration: motion ? 180 : 0
    function tr(key) {
        let currentLanguage = language
        return shelf.trText(key)
    }
}
