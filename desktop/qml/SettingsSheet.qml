import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Sheet {
    id: root
    width: Math.min(parent.width - 48, 840)
    height: Math.min(parent.height - 48, 760)
    property var config: shelf.state.preferences
    property int section: 0
    property int editingTheme: -1
    property string keyboardError: shelf.shortcutError(config.shortcuts || ({}))
    function update(key, value) { let next = Object.assign({}, config); next[key] = value; config = next }
    function setShortcut(key, value) { let shortcuts = Object.assign({}, config.shortcuts); shortcuts[key] = value; update("shortcuts", shortcuts) }
    function applyTheme(values) { if (values.theme) { let next = Object.assign({}, config, values); config = next } }
    function storeTheme(values) {
        if (!values.theme) return
        let themes = (config.custom_themes || []).slice()
        let theme = {}
        let fields = ["theme", "theme_name", "colors", "font_family", "text_scale"]
        fields.forEach(key => theme[key] = values[key] !== undefined ? values[key] : config[key])
        if (editingTheme >= 0) themes[editingTheme] = theme
        else themes.push(theme)
        update("custom_themes", themes)
        applyTheme(Object.assign({}, theme, {theme_style: "custom", custom_theme_index: editingTheme >= 0 ? editingTheme : themes.length - 1}))
        editingTheme = -1
    }
    onOpened: { section = 0; config = JSON.parse(JSON.stringify(shelf.state.preferences)); credential.text = "" }
    ColumnLayout {
        anchors.fill: parent
        spacing: 16
        RowLayout {
            Layout.fillWidth: true
            Text { text: Theme.tr("Settings"); color: Theme.text; font.pixelSize: Theme.px(25); font.weight: Font.DemiBold; Layout.fillWidth: true }
            ActionButton { glyph: "close"; quiet: true; Accessible.name: Theme.tr("Cancel"); onClicked: root.close() }
        }
        SegmentedTabs {
            objectName: "settingsSection"
            Layout.fillWidth: true
            model: [Theme.tr("General"), Theme.tr("Appearance"), Theme.tr("Keyboard")]
            currentIndex: root.section
            onActivated: index => root.section = index
        }
        ScrollView {
            id: settingsScroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth
            ColumnLayout {
                width: settingsScroll.availableWidth
                spacing: 16
                ColumnLayout {
                    visible: root.section === 0
                    Layout.fillWidth: true
                    spacing: 16
                    Text { text: Theme.tr("Language"); color: Theme.text; font.pixelSize: Theme.px(17); font.weight: Font.DemiBold }
                    Choice { Layout.fillWidth: true; model: ["English", "Русский", "Қазақша"]; currentIndex: ["en", "ru", "kk"].indexOf(root.config.language); onActivated: root.update("language", ["en", "ru", "kk"][currentIndex]) }
                    ActionButton { text: Theme.tr("Export library backup…"); glyph: "folder"; onClicked: shelf.exportBackup() }
                    Text { text: Theme.tr("TMDB connection"); color: Theme.text; font.pixelSize: Theme.px(17); font.weight: Font.DemiBold }
                    Text { text: Theme.tr("Use your own API key or Read Access Token. It stays in this user's profile and is not included in library backups."); color: Theme.secondary; font.pixelSize: Theme.px(12); wrapMode: Text.Wrap; Layout.fillWidth: true }
                    Field { id: credential; objectName: "tmdbCredential"; Layout.fillWidth: true; echoMode: TextInput.Password; placeholderText: shelf.tmdb.state.hasKey ? Theme.tr("Personal key saved — leave blank to keep it") : Theme.tr("API key or Read Access Token") }
                    Flow {
                        Layout.fillWidth: true
                        Layout.preferredHeight: childrenRect.height
                        spacing: 8
                        ActionButton { text: Theme.tr("Get a free TMDB key"); onClicked: Qt.openUrlExternally("https://www.themoviedb.org/settings/api") }
                        ActionButton { visible: shelf.tmdb.state.hasKey; text: Theme.tr("Remove key"); destructive: true; onClicked: shelf.tmdb.clearCredential() }
                        ActionButton { text: Theme.tr("Save key"); enabled: credential.text.trim().length > 0; onClicked: { if (shelf.tmdb.saveCredential(credential.text)) credential.text = "" } }
                    }
                    Text { text: Theme.tr("About & credits"); color: Theme.text; font.pixelSize: Theme.px(17); font.weight: Font.DemiBold }
                    Image { source: Qt.resolvedUrl("../assets/tmdb-logo.svg"); Layout.preferredWidth: 65; Layout.preferredHeight: 40; fillMode: Image.PreserveAspectFit }
                    Text { text: "This product uses the TMDB API but is not endorsed or certified by TMDB."; color: Theme.secondary; font.pixelSize: Theme.px(12); wrapMode: Text.Wrap; Layout.fillWidth: true }
                    ActionButton { text: "themoviedb.org"; onClicked: Qt.openUrlExternally("https://www.themoviedb.org") }
                    ActionButton { text: "Medeo Sans · SIL OFL 1.1"; onClicked: Qt.openUrlExternally("https://github.com/DNFDEVS/medeo-font") }
                }
                ColumnLayout {
                    visible: root.section === 1
                    Layout.fillWidth: true
                    spacing: 16
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        Choice {
                            objectName: "themeChoice"
                            model: [Theme.tr("Light theme"), Theme.tr("Dark theme"), Theme.tr("High contrast"), Theme.tr("Custom theme")]
                            currentIndex: ["light", "dark", "contrast", "custom"].indexOf(root.config.theme_style)
                            onActivated: {
                                let key = ["light", "dark", "contrast", "custom"][currentIndex]
                                if (key === "custom") {
                                    let theme = root.config.custom_themes[root.config.custom_theme_index]
                                    if (theme) root.applyTheme(Object.assign({}, theme, {theme_style: key}))
                                    else root.update("theme_style", key)
                                } else root.applyTheme(shelf.themePreset(key))
                            }
                        }
                        ActionButton { text: Theme.tr("Import theme"); onClicked: { root.editingTheme = -1; root.storeTheme(shelf.importTheme()) } }
                        ActionButton { text: Theme.tr("Export theme"); onClicked: shelf.exportTheme(root.config) }
                        Item { Layout.fillWidth: true }
                    }
                    ColumnLayout {
                        visible: root.config.theme_style === "custom"
                        Layout.fillWidth: true
                        Repeater {
                            model: root.config.custom_themes || []
                            delegate: Rectangle {
                                required property var modelData
                                required property int index
                                Layout.fillWidth: true
                                implicitHeight: Theme.px(96)
                                radius: 12
                                color: modelData.colors.background || shelf.themePreset(modelData.theme).colors.background
                                border.color: root.config.custom_theme_index === index ? Theme.accent : Theme.line
                                border.width: root.config.custom_theme_index === index ? 2 : 1
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 14
                                    CheckBox {
                                        checked: root.config.custom_theme_index === index
                                        nextCheckState: function() { return Qt.Checked }
                                        Accessible.name: modelData.theme_name
                                        onClicked: root.applyTheme(Object.assign({}, modelData, {theme_style: "custom", custom_theme_index: index}))
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        Text { text: modelData.theme_name || Theme.tr("My theme"); color: modelData.colors.text || shelf.themePreset(modelData.theme).colors.text; font.family: modelData.font_family; font.pixelSize: Theme.px(18); elide: Text.ElideRight; Layout.fillWidth: true }
                                        Text { text: "MovieShelf · Aa Әә Яя"; color: modelData.colors.secondary || shelf.themePreset(modelData.theme).colors.secondary; font.family: modelData.font_family; font.pixelSize: Theme.px(12) }
                                    }
                                    ActionButton { text: Theme.tr("Edit"); onClicked: { root.editingTheme = index; themeEditor.begin(Object.assign({}, root.config, modelData)) } }
                                }
                            }
                        }
                        ActionButton {
                            text: Theme.tr("Create theme")
                            glyph: "plus"
                            Layout.fillWidth: true
                            implicitHeight: Theme.px(80)
                            onClicked: { root.editingTheme = -1; themeEditor.begin(Object.assign({}, root.config, {theme_name: ""})) }
                        }
                    }
                    Rectangle {
                        visible: root.config.theme_style !== "custom"
                        Layout.fillWidth: true
                        Layout.preferredHeight: Theme.px(80)
                        radius: 12
                        color: root.config.colors.background || shelf.themePreset(root.config.theme).colors.background
                        border.color: root.config.colors.line || shelf.themePreset(root.config.theme).colors.line
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 14
                            Text { text: root.config.theme_name || Theme.tr("Theme preview"); color: root.config.colors.text || shelf.themePreset(root.config.theme).colors.text; font.family: root.config.font_family; font.pixelSize: Math.round(18 * root.config.text_scale) }
                            Text { text: "MovieShelf · Aa Әә Яя"; color: root.config.colors.secondary || shelf.themePreset(root.config.theme).colors.secondary; font.family: root.config.font_family; font.pixelSize: Math.round(12 * root.config.text_scale) }
                        }
                    }
                    Text { text: Theme.tr("Font"); color: Theme.text; font.pixelSize: Theme.px(15) }
                    Choice { objectName: "fontChoice"; Layout.fillWidth: true; model: shelf.fontFamilies; currentIndex: Math.max(0, shelf.fontFamilies.indexOf(root.config.font_family)); onActivated: root.update("font_family", currentText) }
                    Text { text: Theme.tr("Text size") + " · " + Math.round(root.config.text_scale * 100) + "%"; color: Theme.text; font.pixelSize: Theme.px(14) }
                    ScaleSlider { Layout.fillWidth: true; from: 0.85; to: 1.5; stepSize: 0.05; value: root.config.text_scale; Accessible.name: Theme.tr("Text size"); onMoved: root.update("text_scale", Math.round(value * 100) / 100) }
                    Text { text: Theme.tr("Application scale") + " · " + Math.round(root.config.ui_scale * 100) + "%"; color: Theme.text; font.pixelSize: Theme.px(14) }
                    ScaleSlider { Layout.fillWidth: true; from: 0.75; to: 2; stepSize: 0.25; value: root.config.ui_scale; Accessible.name: Theme.tr("Application scale"); onMoved: root.update("ui_scale", value) }
                    Text { text: Theme.tr("Application scale takes effect after restarting MovieShelf."); color: Theme.secondary; font.pixelSize: Theme.px(12); Layout.fillWidth: true; wrapMode: Text.Wrap }
                    Text { text: Theme.tr("Poster size"); color: Theme.text; font.pixelSize: Theme.px(14) }
                    ScaleSlider { Layout.fillWidth: true; from: 155; to: 245; stepSize: 5; value: root.config.card_size; Accessible.name: Theme.tr("Poster size"); onMoved: root.update("card_size", Math.round(value)) }
                    Toggle { text: Theme.tr("Smooth transitions"); checked: root.config.animations; Layout.fillWidth: true; onToggled: root.update("animations", checked) }
                    Toggle { text: Theme.tr("Show collection statistics"); checked: root.config.show_statistics; Layout.fillWidth: true; onToggled: root.update("show_statistics", checked) }
                    ActionButton { text: Theme.tr("Reset text and scale"); onClicked: { root.update("font_family", "Medeo Sans"); root.update("text_scale", 1); root.update("ui_scale", 1) } }
                }
                ColumnLayout {
                    visible: root.section === 2
                    Layout.fillWidth: true
                    spacing: 12
                    Text { text: Theme.tr("Click a shortcut and press your combination. Backspace clears it; Escape cancels."); color: Theme.secondary; wrapMode: Text.Wrap; Layout.fillWidth: true; font.pixelSize: Theme.px(13) }
                    Text { text: Theme.tr("Tab and Shift+Tab move focus. Enter or Space activates a control. Escape closes a dialog."); color: Theme.secondary; wrapMode: Text.Wrap; Layout.fillWidth: true; font.pixelSize: Theme.px(13) }
                    Text { visible: !!root.keyboardError; text: root.keyboardError; color: Theme.danger; wrapMode: Text.Wrap; Layout.fillWidth: true; font.pixelSize: Theme.px(13) }
                    Repeater {
                        model: shelf.keyboardActions
                        delegate: ColumnLayout {
                            required property var modelData
                            required property int index
                            Layout.fillWidth: true
                            Text { visible: index === 0 || shelf.keyboardActions[index - 1].group !== modelData.group; text: Theme.tr(modelData.group); color: Theme.accent; font.pixelSize: Theme.px(14); font.weight: Font.DemiBold; Layout.topMargin: 12 }
                            RowLayout {
                                Layout.fillWidth: true
                                Text { text: Theme.tr(modelData.title); color: Theme.text; font.pixelSize: Theme.px(13); Layout.fillWidth: true; wrapMode: Text.Wrap }
                                ShortcutRecorder { objectName: "shortcut_" + modelData.id; sequence: root.config.shortcuts[modelData.id] || ""; onRecorded: value => root.setShortcut(modelData.id, value) }
                                ActionButton { text: Theme.tr("Reset"); quiet: true; onClicked: root.setShortcut(modelData.id, modelData.default) }
                            }
                        }
                    }
                    ActionButton { text: Theme.tr("Reset all shortcuts"); onClicked: { let shortcuts = {}; shelf.keyboardActions.forEach(action => shortcuts[action.id] = action.default); root.update("shortcuts", shortcuts) } }
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Text { text: "MovieShelf " + Qt.application.version; color: Theme.secondary; font.pixelSize: Theme.px(11) }
            Item { Layout.fillWidth: true }
            ActionButton { text: Theme.tr("Cancel"); quiet: true; onClicked: root.close() }
            ActionButton { objectName: "saveSettingsButton"; text: Theme.tr("Save and apply"); primary: true; enabled: !root.keyboardError; onClicked: { if (shelf.saveSettings(root.config)) root.close() } }
        }
    }
    ThemeEditor { id: themeEditor; onThemeCreated: values => root.storeTheme(values) }
}
