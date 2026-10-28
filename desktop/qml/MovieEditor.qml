import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Sheet {
    id: root
    width: Math.min(parent.width - 48, 1000)
    height: Math.min(parent.height - 48, 760)
    closePolicy: Popup.NoAutoClose
    property int tab: 0
    property bool closeApplication: false
    property var movie: shelf.draft
    signal quitRequested()
    onOpened: { tab = 0; closeApplication = false; titleInput.forceActiveFocus() }
    function requestClose() {
        if (shelf.dirty) unsaved.open()
        else finishClose()
    }
    function finishClose() {
        root.close()
        if (closeApplication) quitRequested()
    }
    Shortcut { sequence: "Ctrl+S"; enabled: root.opened; onActivated: shelf.saveMovie(false) }
    Shortcut { sequence: "Escape"; enabled: root.opened && !unsaved.opened && !deleteConfirm.opened; onActivated: root.requestClose() }
    component Caption: Text { color: Theme.secondary; font.pixelSize: 12; font.weight: Font.Medium }
    ColumnLayout {
        anchors.fill: parent
        spacing: 20
        RowLayout {
            Layout.fillWidth: true
            ColumnLayout {
                spacing: 4
                Text { text: Theme.tr(root.movie.id ? "Edit movie" : "Add a movie"); color: Theme.text; font.pixelSize: 26; font.weight: Font.DemiBold; font.letterSpacing: -0.5 }
                Caption { text: (root.movie.id ? "ID #" + root.movie.id : Theme.tr("ID assigned on save")) + (shelf.dirty ? "  ·  " + Theme.tr("Unsaved changes") : "") }
            }
            Item { Layout.fillWidth: true }
            ActionButton { glyph: "close"; quiet: true; Accessible.name: Theme.tr("Cancel"); onClicked: root.requestClose() }
        }
        Rectangle {
            Layout.fillWidth: true
            height: 43
            radius: 11
            color: Theme.elevated
            RowLayout {
                anchors.fill: parent
                anchors.margins: 4
                spacing: 3
                Repeater {
                    model: ["Overview", "Movie Review", "Organization", "Poster studio"]
                    delegate: Button {
                        id: tabButton
                        required property string modelData
                        required property int index
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        onClicked: root.tab = index
                        contentItem: Text { text: Theme.tr(tabButton.modelData); color: root.tab === tabButton.index ? Theme.text : Theme.secondary; font.pixelSize: 13; font.weight: root.tab === tabButton.index ? Font.DemiBold : Font.Normal; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        background: Rectangle { radius: 8; color: root.tab === tabButton.index ? Theme.surface : "transparent"; border.width: tabButton.activeFocus ? 1 : 0; border.color: Theme.accent; Behavior on color { ColorAnimation { duration: Theme.duration } } }
                    }
                }
            }
        }
        StackLayout {
            currentIndex: root.tab
            Layout.fillWidth: true
            Layout.fillHeight: true
            ScrollView {
                id: overviewScroll
                clip: true
                contentWidth: availableWidth
                contentHeight: overviewRow.implicitHeight
                RowLayout {
                    id: overviewRow
                    width: overviewScroll.availableWidth
                    spacing: 28
                    ColumnLayout {
                        Layout.alignment: Qt.AlignTop
                        Layout.preferredWidth: 210
                        spacing: 12
                        Poster { Layout.preferredWidth: 210; Layout.preferredHeight: 315; source: root.movie.posterUrl || ""; crop: root.movie.poster_crop || ({zoom: 1, x: 0, y: 0, mode: "fill"}); editable: true; onDropped: url => shelf.loadPoster(url); onRepositioned: (x, y) => { shelf.setCrop("x", x); shelf.setCrop("y", y) } }
                        ActionButton { text: Theme.tr("Choose poster…"); glyph: "image"; Layout.fillWidth: true; onClicked: shelf.choosePoster() }
                        Caption { text: Theme.tr("Drop an image here"); Layout.alignment: Qt.AlignHCenter; font.pixelSize: 11 }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignTop
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 10
                            Caption { text: Theme.tr("Title") }
                            Field { id: titleInput; objectName: "titleInput"; Layout.fillWidth: true; text: root.movie.title || ""; placeholderText: Theme.tr("The name of your next favorite film"); onTextEdited: shelf.updateDraft("title", text) }
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 16
                                ColumnLayout {
                                    Layout.preferredWidth: 130
                                    Layout.maximumWidth: 140
                                    Caption { text: Theme.tr("Release year") }
                                    Field { objectName: "yearInput"; Layout.fillWidth: true; text: String(root.movie.year || ""); validator: IntValidator { bottom: 1888; top: 2100 } onTextEdited: shelf.updateDraft("year", text) }
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    Caption { text: Theme.tr("Status") }
                                    Choice { Layout.fillWidth: true; model: [Theme.tr("Want to watch"), Theme.tr("Watched")]; currentIndex: root.movie.status === "watched" ? 1 : 0; onActivated: shelf.updateDraft("status", currentIndex ? "watched" : "watchlist") }
                                }
                            }
                            Toggle { text: Theme.tr("Keep in Favorites"); checked: root.movie.favorite || false; onToggled: shelf.updateDraft("favorite", checked) }
                            Caption { text: Theme.tr("Description") }
                            NotesField { Layout.fillWidth: true; Layout.preferredHeight: 180; text: root.movie.description || ""; placeholderText: Theme.tr("What is this film about? Add a synopsis or your own notes."); onEdited: value => { if (root.opened) shelf.updateDraft("description", value) } }
                        }
                    }
                }
            }
            ColumnLayout {
                spacing: 16
                Caption { text: Theme.tr("Your rating") }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    Repeater {
                        model: 10
                        delegate: ActionButton {
                            required property int index
                            text: String(index + 1)
                            Layout.fillWidth: true
                            primary: root.movie.rating === index + 1
                            onClicked: shelf.updateDraft("rating", index + 1)
                        }
                    }
                    ActionButton { glyph: "close"; quiet: true; Accessible.name: Theme.tr("Not rated"); onClicked: shelf.updateDraft("rating", 0) }
                }
                Text { text: root.movie.rating ? "★ " + root.movie.rating + " / 10" : Theme.tr("Not rated"); color: Theme.gold; font.pixelSize: 20; font.weight: Font.DemiBold }
                Caption { text: Theme.tr("My review") }
                NotesField { objectName: "reviewInput"; Layout.fillWidth: true; Layout.fillHeight: true; text: root.movie.review || ""; placeholderText: Theme.tr("Your personal review. What worked? How did it make you feel? Would you watch it again?"); onEdited: value => { if (root.opened) shelf.updateDraft("review", value) } }
            }
            ScrollView {
                clip: true
                contentWidth: availableWidth
                ColumnLayout {
                    width: parent.width
                    spacing: 12
                    Caption { text: Theme.tr("Genres") }
                    Field { Layout.fillWidth: true; text: root.movie.genresText || ""; placeholderText: Theme.tr("Separate names with commas"); onTextEdited: shelf.updateDraft("genresText", text) }
                    Caption { text: Theme.tr("Tags"); Layout.topMargin: 8 }
                    Field { Layout.fillWidth: true; text: root.movie.tagsText || ""; placeholderText: Theme.tr("Separate names with commas"); onTextEdited: shelf.updateDraft("tagsText", text) }
                    Caption { text: Theme.tr("Choose collections for this movie"); Layout.topMargin: 16 }
                    Repeater {
                        model: shelf.state.collections
                        delegate: Toggle {
                            required property var modelData
                            Layout.fillWidth: true
                            text: modelData.name
                            checked: (root.movie.collections || []).indexOf(modelData.id) >= 0
                            onToggled: shelf.selectCollection(modelData.id, checked)
                        }
                    }
                    Text { visible: shelf.state.collections.length === 0; text: Theme.tr("Create collections from the sidebar."); color: Theme.secondary; font.pixelSize: 13 }
                }
            }
            ScrollView {
                clip: true
                contentWidth: availableWidth
                ColumnLayout {
                    width: parent.width
                    spacing: 20
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 28
                        Poster {
                            objectName: "cropPoster"
                            Layout.preferredWidth: 220
                            Layout.preferredHeight: 330
                            source: root.movie.posterUrl || ""
                            crop: root.movie.poster_crop || ({zoom: 1, x: 0, y: 0, mode: "fill"})
                            editable: true
                            onDropped: url => shelf.loadPoster(url)
                            onRepositioned: (x, y) => { shelf.setCrop("x", x); shelf.setCrop("y", y) }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 10
                            Caption { text: Theme.tr("Poster position") }
                            Text { text: Theme.tr("Drag the poster to reposition it.\nAdjust the scale to frame your favorite detail."); color: Theme.secondary; font.pixelSize: 13; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                            ActionButton { text: Theme.tr("Choose poster…"); glyph: "image"; onClicked: shelf.choosePoster() }
                            Choice { Layout.fillWidth: true; model: [Theme.tr("Fill the frame"), Theme.tr("Show full image")]; currentIndex: root.movie.poster_crop && root.movie.poster_crop.mode === "fit" ? 1 : 0; onActivated: shelf.setCropMode(currentIndex ? "fit" : "fill") }
                            Repeater {
                                model: [{key: "zoom", title: "Scale", min: 1, max: 3}, {key: "x", title: "Horizontal position", min: -1, max: 1}, {key: "y", title: "Vertical position", min: -1, max: 1}]
                                delegate: RowLayout {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    Caption { text: Theme.tr(modelData.title); Layout.preferredWidth: 140 }
                                    ScaleSlider { Layout.fillWidth: true; from: modelData.min; to: modelData.max; value: root.movie.poster_crop ? root.movie.poster_crop[modelData.key] : modelData.min; onMoved: shelf.setCrop(modelData.key, value); Accessible.name: Theme.tr(modelData.title) }
                                }
                            }
                            RowLayout {
                                ActionButton { text: Theme.tr("Reset framing"); quiet: true; onClicked: shelf.resetCrop() }
                                ActionButton { text: Theme.tr("Remove poster"); destructive: true; quiet: true; onClicked: shelf.removePoster() }
                            }
                        }
                    }
                    Caption { text: Theme.tr("Preview at card sizes") }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 22
                        Repeater {
                            model: [{size: 135, title: "Small"}, {size: 180, title: "Medium"}, {size: 225, title: "Large"}]
                            delegate: ColumnLayout {
                                required property var modelData
                                spacing: 10
                                Layout.alignment: Qt.AlignTop
                                Poster { Layout.preferredWidth: modelData.size; Layout.preferredHeight: modelData.size * 1.5; source: root.movie.posterUrl || ""; crop: root.movie.poster_crop || ({zoom: 1, x: 0, y: 0, mode: "fill"}) }
                                Caption { text: Theme.tr(modelData.title); Layout.alignment: Qt.AlignHCenter }
                            }
                        }
                        Item { Layout.fillWidth: true }
                    }
                }
            }
        }
        Rectangle { Layout.fillWidth: true; height: 1; color: Theme.line }
        RowLayout {
            Layout.fillWidth: true
            ActionButton { visible: !!root.movie.id; glyph: "trash"; destructive: true; quiet: true; Accessible.name: Theme.tr("Delete movie"); onClicked: deleteConfirm.open() }
            Item { Layout.fillWidth: true }
            ActionButton { text: Theme.tr("Cancel"); quiet: true; onClicked: root.requestClose() }
            ActionButton { objectName: "saveMovieButton"; text: Theme.tr("Save"); onClicked: shelf.saveMovie(false) }
            ActionButton { text: Theme.tr("Save & view"); primary: true; onClicked: shelf.saveMovie(true) }
        }
    }
    Sheet {
        id: unsaved
        objectName: "unsavedSheet"
        width: Math.min(parent.width - 60, 530)
        height: 215
        z: 20
        onClosed: if (root.opened) root.closeApplication = false
        ColumnLayout {
            anchors.fill: parent
            spacing: 18
            Text { text: Theme.tr("Unsaved changes"); font.pixelSize: 22; font.weight: Font.DemiBold; color: Theme.text }
            Text { text: Theme.tr("Save your changes before closing?"); color: Theme.secondary; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            RowLayout {
                Layout.fillWidth: true
                ActionButton { objectName: "cancelUnsavedButton"; text: Theme.tr("Cancel"); quiet: true; onClicked: { root.closeApplication = false; unsaved.close() } }
                Item { Layout.fillWidth: true }
                ActionButton { objectName: "discardUnsavedButton"; text: Theme.tr("Discard"); destructive: true; onClicked: { root.finishClose(); unsaved.close() } }
                ActionButton { objectName: "saveUnsavedButton"; text: Theme.tr("Save"); primary: true; onClicked: { if (shelf.saveMovie(false)) { root.finishClose(); unsaved.close() } } }
            }
        }
    }
    Sheet {
        id: deleteConfirm
        width: Math.min(parent.width - 60, 480)
        height: 210
        z: 20
        ColumnLayout {
            anchors.fill: parent
            spacing: 18
            Text { text: Theme.tr("Delete movie"); color: Theme.text; font.pixelSize: 22; font.weight: Font.DemiBold }
            Text { text: Theme.tr("Delete “{title}” and its review?").replace("{title}", root.movie.title || ""); color: Theme.secondary; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            RowLayout {
                Layout.alignment: Qt.AlignRight
                ActionButton { text: Theme.tr("Cancel"); onClicked: deleteConfirm.close() }
                ActionButton { text: Theme.tr("Delete"); destructive: true; onClicked: { if (shelf.deleteMovie(root.movie.id)) { deleteConfirm.close(); root.close() } } }
            }
        }
    }
}
