import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    objectName: "mainWindow"
    width: 1240
    height: 840
    minimumWidth: 860
    minimumHeight: 620
    visible: true
    title: "MovieShelf"
    color: Theme.background
    font.family: Qt.application.font.family
    font.pixelSize: 14
    palette.window: Theme.background
    palette.windowText: Theme.text
    palette.text: Theme.text
    palette.base: Theme.surface
    palette.button: Theme.elevated
    palette.buttonText: Theme.text
    palette.highlight: Theme.accent
    property bool filtersOpen: false
    property bool quitting: false
    function navigate(view) { shelf.setView(view); gallery.positionViewAtBeginning(); pageFade.restart() }
    function openSearch() { searchField.text = shelf.state.query; searchSheet.open() }
    onClosing: close => {
        if (editor.opened && shelf.dirty && !quitting) {
            close.accepted = false
            editor.closeApplication = true
            editor.requestClose()
        }
    }
    Shortcut { sequence: "Ctrl+N"; enabled: !editor.opened && !settings.opened; onActivated: shelf.editMovie(0) }
    Shortcut { sequence: "Ctrl+F"; enabled: !editor.opened && !settings.opened; onActivated: window.openSearch() }
    Rectangle {
        id: sidebar
        width: window.width < 1050 ? 205 : 226
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        color: Theme.sidebar
        Rectangle { width: 1; anchors.right: parent.right; height: parent.height; color: Theme.line }
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            anchors.topMargin: 34
            anchors.bottomMargin: 24
            spacing: 7
            RowLayout {
                Layout.leftMargin: 12
                Layout.bottomMargin: 34
                spacing: 11
                Text { text: "MovieShelf"; font.pixelSize: 21; font.weight: Font.DemiBold; font.letterSpacing: -0.6; color: Theme.text }
            }
            Text { text: Theme.tr("COLLECTION"); color: Theme.secondary; font.pixelSize: 10; font.weight: Font.DemiBold; font.letterSpacing: 1.4; Layout.leftMargin: 13; Layout.bottomMargin: 5 }
            Repeater {
                model: [{key: "Library", icon: "library"}, {key: "Watchlist", icon: "watchlist"}, {key: "Watched", icon: "watched"}, {key: "Favorites", icon: "favorite"}, {key: "My reviews", icon: "reviews"}]
                delegate: Button {
                    id: nav
                    required property var modelData
                    readonly property bool selected: shelf.state.view === modelData.key
                    Layout.fillWidth: true
                    implicitHeight: 44
                    hoverEnabled: true
                    onClicked: window.navigate(modelData.key)
                    Accessible.name: Theme.tr(modelData.key)
                    background: Rectangle { radius: 11; color: nav.selected ? Theme.selected : nav.hovered ? Theme.hover : Theme.sidebar; border.width: nav.activeFocus ? 1 : 0; border.color: Theme.accent; Behavior on color { ColorAnimation { duration: Theme.duration } } }
                    contentItem: RowLayout {
                        spacing: 12
                        Glyph { name: nav.modelData.icon; ink: nav.selected ? Theme.accent : Theme.secondary; Layout.leftMargin: 13; width: 19; height: 19 }
                        Text { text: Theme.tr(nav.modelData.key); Layout.fillWidth: true; color: nav.selected ? Theme.accent : Theme.text; font.pixelSize: 13; font.weight: nav.selected ? Font.DemiBold : Font.Normal; elide: Text.ElideRight }
                        Text { text: shelf.state.total; visible: nav.modelData.key === "Library"; color: Theme.secondary; font.pixelSize: 11; Layout.rightMargin: 12 }
                    }
                }
            }
            RowLayout {
                Layout.topMargin: 27
                Layout.leftMargin: 13
                Layout.fillWidth: true
                Text { text: Theme.tr("Collections"); color: Theme.secondary; font.pixelSize: 12; Layout.fillWidth: true }
                ActionButton { glyph: "plus"; quiet: true; implicitHeight: 28; implicitWidth: 28; Accessible.name: Theme.tr("Manage collections"); onClicked: collections.open() }
            }
            ListView {
                Layout.fillWidth: true
                Layout.preferredHeight: Math.min(contentHeight, 200)
                clip: true
                model: shelf.state.collections
                spacing: 4
                delegate: Button {
                    id: collectionNav
                    required property var modelData
                    width: ListView.view.width
                    height: 39
                    hoverEnabled: true
                    onClicked: window.navigate("collection:" + modelData.id)
                    background: Rectangle { radius: 10; color: shelf.state.view === "collection:" + collectionNav.modelData.id ? Theme.selected : collectionNav.hovered ? Theme.hover : Theme.sidebar }
                    contentItem: RowLayout {
                        Glyph { name: "folder"; width: 18; height: 18; Layout.leftMargin: 13 }
                        Text { text: collectionNav.modelData.name; textFormat: Text.PlainText; color: Theme.text; font.pixelSize: 13; Layout.fillWidth: true; elide: Text.ElideRight }
                    }
                }
                ScrollIndicator.vertical: ScrollIndicator {}
            }
            Item { Layout.fillHeight: true }
            ActionButton { text: Theme.tr("Settings"); glyph: "settings"; quiet: true; Layout.fillWidth: true; onClicked: settings.open() }
            Text { text: "v1.3.0"; font.pixelSize: 11; color: Theme.secondary; Layout.alignment: Qt.AlignHCenter; Layout.topMargin: 10 }
        }
    }
    ColumnLayout {
        anchors { left: sidebar.right; right: parent.right; top: parent.top; bottom: parent.bottom; margins: 34; bottomMargin: 18 }
        spacing: 22
        RowLayout {
            Layout.fillWidth: true
            spacing: 12
            Text { text: shelf.state.title; textFormat: Text.PlainText; color: Theme.text; font.pixelSize: 32; font.weight: Font.DemiBold; font.letterSpacing: -1; Layout.fillWidth: true; elide: Text.ElideRight }
            ActionButton { objectName: "searchButton"; glyph: "search"; quiet: true; Accessible.name: Theme.tr("Search (Ctrl+F)"); onClicked: window.openSearch() }
            ActionButton { text: Theme.tr("Add a movie"); glyph: "plus"; primary: true; onClicked: shelf.editMovie(0) }
        }
        RowLayout {
            visible: shelf.state.preferences.show_statistics
            Layout.fillWidth: true
            spacing: 24
            Repeater {
                model: [{value: shelf.state.total, key: "In your library"}, {value: shelf.state.watched, key: "Watched"}, {value: shelf.state.average, key: "Average rating"}]
                delegate: Row {
                    required property var modelData
                    spacing: 7
                    Text { text: modelData.value; color: Theme.text; font.pixelSize: 14; font.weight: Font.DemiBold }
                    Text { text: Theme.tr(modelData.key); color: Theme.secondary; font.pixelSize: 13 }
                }
            }
            Item { Layout.fillWidth: true }
        }
        Rectangle { Layout.fillWidth: true; height: 1; color: Theme.line }
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            ActionButton {
                text: Theme.tr("Filters") + (shelf.state.filterCount ? " · " + shelf.state.filterCount : "")
                glyph: "filter"
                foreground: window.filtersOpen || shelf.state.filterCount ? Theme.accent : Theme.text
                onClicked: window.filtersOpen = !window.filtersOpen
            }
            ActionButton { visible: shelf.state.query !== ""; text: shelf.state.query.length > 18 ? shelf.state.query.slice(0, 18) + "…" : shelf.state.query; glyph: "close"; onClicked: shelf.setQuery("") }
            Item { Layout.fillWidth: true }
            Choice { Layout.preferredWidth: 185; model: [Theme.tr("Recently added"), Theme.tr("Title A–Z"), Theme.tr("Highest rated"), Theme.tr("Newest release")]; currentIndex: shelf.state.sort; onActivated: shelf.setSort(currentIndex) }
        }
        FilterPanel { visible: window.filtersOpen; Layout.fillWidth: true }
        RowLayout {
            Layout.fillWidth: true
            Text { text: shelf.state.resultLabel; color: Theme.secondary; font.pixelSize: 13 }
            Item { Layout.fillWidth: true }
            Glyph { name: "image"; width: 16; height: 16 }
            ScaleSlider {
                id: sizeSlider
                objectName: "cardSizeSlider"
                Layout.preferredWidth: 110
                from: 155; to: 245; stepSize: 5
                value: shelf.state.preferences.card_size
                Accessible.name: Theme.tr("Poster size")
                onPressedChanged: if (!pressed) shelf.saveCardSize(Math.round(value))
                onMoved: sizeSave.restart()
                Timer { id: sizeSave; interval: 600; onTriggered: if (!sizeSlider.pressed) shelf.saveCardSize(Math.round(sizeSlider.value)) }
            }
        }
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            GridView {
                id: gallery
                objectName: "movieGrid"
                anchors.fill: parent
                clip: true
                model: shelf.movieModel
                readonly property int columns: Math.max(1, Math.floor(width / (sizeSlider.value + 24)))
                cellWidth: width / columns
                cellHeight: sizeSlider.value * 1.5 + (shelf.state.view === "My reviews" ? 130 : 90)
                cacheBuffer: cellHeight
                reuseItems: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                delegate: Item {
                    id: card
                    required property var film
                    required property int index
                    width: gallery.cellWidth
                    height: gallery.cellHeight
                    Column {
                        id: cardBody
                        width: sizeSlider.value
                        x: 2
                        y: hover.hovered ? 0 : 3
                        spacing: 9
                        Behavior on y { NumberAnimation { duration: Theme.duration; easing.type: Easing.OutCubic } }
                        Poster { width: parent.width; height: width * 1.5; source: card.film.posterUrl; crop: card.film.poster_crop }
                        Text { text: card.film.title; textFormat: Text.PlainText; width: parent.width; elide: Text.ElideRight; color: Theme.text; font.pixelSize: 14; font.weight: Font.DemiBold }
                        RowLayout {
                            width: parent.width
                            Text { text: card.film.year + "  ·  #" + card.film.id; color: Theme.secondary; font.pixelSize: 12 }
                            Item { Layout.fillWidth: true }
                            Text { text: card.film.rating ? "★ " + card.film.rating : ""; color: Theme.gold; font.pixelSize: 12; font.weight: Font.DemiBold }
                            Glyph { visible: card.film.favorite; name: "favorite"; width: 13; height: 13; ink: Theme.accent }
                        }
                        Text { text: Theme.tr(card.film.status === "watched" ? "Watched" : "Want to watch"); color: Theme.secondary; font.pixelSize: 11 }
                        Text { visible: shelf.state.view === "My reviews"; text: card.film.review || Theme.tr("No written review yet."); textFormat: Text.PlainText; color: Theme.secondary; width: parent.width; font.pixelSize: 12; maximumLineCount: 2; elide: Text.ElideRight; wrapMode: Text.WordWrap }
                    }
                    HoverHandler { id: hover }
                    MouseArea { width: cardBody.width; height: cardBody.height; cursorShape: Qt.PointingHandCursor; onClicked: shelf.previewMovie(card.film.id) }
                    Accessible.role: Accessible.Button
                    Accessible.name: film.title + ", " + film.year
                    Accessible.onPressAction: shelf.previewMovie(film.id)
                    activeFocusOnTab: true
                    Keys.onReturnPressed: shelf.previewMovie(film.id)
                    Rectangle { anchors.fill: cardBody; anchors.margins: -3; color: "transparent"; radius: 14; border.width: card.activeFocus ? 2 : 0; border.color: Theme.accent }
                }
            }
            Column {
                visible: shelf.state.resultCount === 0
                anchors.centerIn: parent
                spacing: 18
                Rectangle {
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: 76; height: 76; radius: 23; color: Theme.elevated
                    Glyph { anchors.centerIn: parent; name: "library"; width: 32; height: 32; ink: Theme.accent }
                }
                Text { text: Theme.tr("A little room for your next discovery."); color: Theme.text; font.pixelSize: 18; anchors.horizontalCenter: parent.horizontalCenter }
                Text { text: Theme.tr("Try another search, or add a film to your collection."); color: Theme.secondary; font.pixelSize: 13; anchors.horizontalCenter: parent.horizontalCenter }
                ActionButton { text: Theme.tr("Add a movie"); primary: true; anchors.horizontalCenter: parent.horizontalCenter; onClicked: shelf.editMovie(0) }
            }
        }
    }
    NumberAnimation { id: pageFade; target: gallery; property: "opacity"; from: 0.3; to: 1; duration: Theme.duration }
    Sheet {
        id: searchSheet
        objectName: "searchSheet"
        width: Math.min(window.width - 80, 680)
        height: 190
        onOpened: searchField.forceActiveFocus()
        ColumnLayout {
            anchors.fill: parent
            spacing: 17
            RowLayout {
                Glyph { name: "search"; ink: Theme.accent }
                Field { id: searchField; objectName: "searchInput"; Layout.fillWidth: true; font.pixelSize: 20; implicitHeight: 54; placeholderText: Theme.tr("Search your collection…"); onAccepted: { shelf.setQuery(text); window.navigate("Library"); searchSheet.close() } }
            }
            RowLayout {
                Text { text: "Esc · " + Theme.tr("Cancel"); color: Theme.secondary; font.pixelSize: 12 }
                Item { Layout.fillWidth: true }
                ActionButton { text: Theme.tr("Show results in library"); primary: true; onClicked: { shelf.setQuery(searchField.text); window.navigate("Library"); searchSheet.close() } }
            }
        }
    }
    MovieEditor { id: editor; objectName: "movieEditor"; onQuitRequested: { window.quitting = true; window.close() } }
    MovieDetails { id: details; objectName: "movieDetails" }
    SettingsSheet { id: settings; objectName: "settingsSheet" }
    CollectionsSheet { id: collections; objectName: "collectionsSheet" }
    Sheet {
        id: errorSheet
        objectName: "errorSheet"
        property string message: ""
        width: Math.min(window.width - 80, 520)
        height: Math.min(window.height - 80, errorContent.implicitHeight + 56)
        z: 100
        ColumnLayout {
            id: errorContent
            anchors.fill: parent
            spacing: 20
            Text { text: Theme.tr("Something went wrong"); color: Theme.text; font.pixelSize: 21; font.weight: Font.DemiBold }
            Text { text: errorSheet.message; textFormat: Text.PlainText; color: Theme.secondary; wrapMode: Text.Wrap; Layout.fillWidth: true }
            ActionButton { text: Theme.tr("Done"); primary: true; Layout.alignment: Qt.AlignRight; onClicked: errorSheet.close() }
        }
    }
    Rectangle {
        id: toast
        property string message: ""
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 24
        width: Math.min(window.width - 60, toastText.implicitWidth + 40)
        height: toastText.implicitHeight + 24
        radius: 13
        color: Theme.elevated
        border.color: Theme.line
        opacity: toastTimer.running ? 1 : 0
        visible: opacity > 0
        Behavior on opacity { NumberAnimation { duration: Theme.duration } }
        Text { id: toastText; text: toast.message; anchors.centerIn: parent; color: Theme.text; font.pixelSize: 13 }
        Timer { id: toastTimer; interval: 3000 }
    }
    Connections {
        target: shelf
        function onEditorRequested() { details.close(); editor.open() }
        function onPreviewRequested() { details.open() }
        function onMovieSaved(viewAfter) { if (viewAfter) { editor.close(); details.open() } }
        function onErrorOccurred(message) { errorSheet.message = message; errorSheet.open() }
        function onNotified(message) { toast.message = message; toastTimer.restart() }
    }
}
