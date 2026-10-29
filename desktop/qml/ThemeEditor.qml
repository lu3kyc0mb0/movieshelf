import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Sheet {
    id: root
    objectName: "themeEditor"
    z: 30
    width: Math.min(parent.width - 48, 760)
    height: Math.min(parent.height - 48, 720)
    property var draft: shelf.state.preferences
    readonly property string validationError: shelf.themeError(draft)
    property var colorFields: [
        {key: "background", name: "Background"}, {key: "sidebar", name: "Sidebar"},
        {key: "surface", name: "Dialogs"}, {key: "elevated", name: "Controls"},
        {key: "hover", name: "Hover"}, {key: "line", name: "Borders"},
        {key: "text", name: "Text"}, {key: "secondary", name: "Secondary text"},
        {key: "accent", name: "Accent"}, {key: "onAccent", name: "Text on accent"},
        {key: "selected", name: "Selection"}, {key: "danger", name: "Errors"}, {key: "gold", name: "Ratings"}
    ]
    signal themeCreated(var values)
    function begin(values) {
        let next = JSON.parse(JSON.stringify(values))
        next.theme_style = "custom"
        if (!next.theme_name) next.theme_name = Theme.tr("My theme")
        draft = next
        open()
    }
    function update(key, value) { let next = Object.assign({}, draft); next[key] = value; draft = next }
    function colorValue(key) {
        let value = draft.colors[key]
        return typeof value === "string" && /^#[0-9a-f]{6}$/i.test(value) ? value : shelf.themePreset(draft.theme).colors[key]
    }
    function setColor(key, value) { let colors = Object.assign({}, draft.colors); colors[key] = value; update("colors", colors) }
    ColumnLayout {
        anchors.fill: parent
        spacing: 16
        RowLayout {
            Layout.fillWidth: true
            Text { text: Theme.tr("Create theme"); color: Theme.text; font.pixelSize: Theme.px(23); font.weight: Font.DemiBold; Layout.fillWidth: true }
            ActionButton { glyph: "close"; quiet: true; Accessible.name: Theme.tr("Cancel"); onClicked: root.close() }
        }
        ScrollView {
            id: editorScroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth
            ColumnLayout {
                width: editorScroll.availableWidth
                spacing: 15
                Text { text: Theme.tr("Theme name"); color: Theme.text; font.pixelSize: Theme.px(13) }
                Field { objectName: "customThemeName"; Layout.fillWidth: true; text: root.draft.theme_name || ""; onTextEdited: root.update("theme_name", text) }
                Text { text: Theme.tr("Base colors"); color: Theme.text; font.pixelSize: Theme.px(13) }
                Choice {
                    Layout.fillWidth: true
                    model: [Theme.tr("Light theme"), Theme.tr("Dark theme")]
                    currentIndex: root.draft.theme === "light" ? 0 : 1
                    onActivated: {
                        let preset = shelf.themePreset(currentIndex === 0 ? "light" : "dark")
                        root.draft = Object.assign({}, root.draft, {theme: preset.theme, colors: preset.colors})
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Theme.px(94)
                    radius: 12
                    color: root.colorValue("background")
                    border.color: root.colorValue("line")
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: root.draft.theme_name || Theme.tr("Theme preview"); color: root.colorValue("text"); font.family: root.draft.font_family; font.pixelSize: Math.round(18 * root.draft.text_scale) }
                            Text { text: "MovieShelf · Aa Әә Яя"; color: root.colorValue("secondary"); font.family: root.draft.font_family; font.pixelSize: Math.round(13 * root.draft.text_scale) }
                        }
                        Rectangle {
                            Layout.preferredWidth: Theme.px(85)
                            Layout.preferredHeight: Theme.px(40)
                            radius: 10
                            color: root.colorValue("accent")
                            Text { anchors.centerIn: parent; text: Theme.tr("Save"); color: root.colorValue("onAccent"); font.family: root.draft.font_family; font.pixelSize: Math.round(13 * root.draft.text_scale) }
                        }
                    }
                }
                Text { text: Theme.tr("Font"); color: Theme.text; font.pixelSize: Theme.px(13) }
                Choice { objectName: "customThemeFont"; Layout.fillWidth: true; model: shelf.fontFamilies; currentIndex: Math.max(0, shelf.fontFamilies.indexOf(root.draft.font_family)); onActivated: root.update("font_family", currentText) }
                Text { text: Theme.tr("Text size") + " · " + Math.round(root.draft.text_scale * 100) + "%"; color: Theme.text; font.pixelSize: Theme.px(13) }
                ScaleSlider { Layout.fillWidth: true; from: 0.85; to: 1.5; stepSize: 0.05; value: root.draft.text_scale; Accessible.name: Theme.tr("Text size"); onMoved: root.update("text_scale", Math.round(value * 100) / 100) }
                Text { text: Theme.tr("Colors"); color: Theme.text; font.pixelSize: Theme.px(17); font.weight: Font.DemiBold; Layout.topMargin: 8 }
                Repeater {
                    model: root.colorFields
                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        Text { text: Theme.tr(modelData.name); color: Theme.text; font.pixelSize: Theme.px(13); Layout.fillWidth: true; wrapMode: Text.Wrap }
                        Field { Layout.preferredWidth: 135; maximumLength: 7; text: root.draft.colors[modelData.key] || shelf.themePreset(root.draft.theme).colors[modelData.key]; Accessible.name: Theme.tr(modelData.name); onTextEdited: root.setColor(modelData.key, text) }
                        Rectangle { Layout.preferredWidth: 24; Layout.preferredHeight: 24; radius: 5; color: root.colorValue(modelData.key); border.color: Theme.secondary }
                        ActionButton { text: Theme.tr("Choose color"); onClicked: root.setColor(modelData.key, shelf.chooseThemeColor(root.colorValue(modelData.key))) }
                    }
                }
            }
        }
        Text { visible: !!root.validationError; text: root.validationError; color: Theme.danger; font.pixelSize: Theme.px(12); Layout.fillWidth: true; wrapMode: Text.Wrap }
        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            ActionButton { text: Theme.tr("Cancel"); quiet: true; onClicked: root.close() }
            ActionButton { objectName: "applyCustomTheme"; text: Theme.tr("Use theme"); primary: true; enabled: !root.validationError; onClicked: { root.themeCreated(root.draft); root.close() } }
        }
    }
}
