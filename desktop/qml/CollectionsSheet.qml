import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Sheet {
    id: root
    width: Math.min(parent.width - 60, 610)
    height: Math.min(parent.height - 60, 570)
    property string selectedId: ""
    property string deleteId: ""
    property string selectedName: ""
    onOpened: { selectedId = ""; nameInput.text = "" }
    ColumnLayout {
        anchors.fill: parent
        spacing: 20
        RowLayout {
            Layout.fillWidth: true
            Text { text: Theme.tr("Collections"); color: Theme.text; font.pixelSize: Theme.px(27); font.weight: Font.DemiBold; Layout.fillWidth: true }
            ActionButton { glyph: "close"; quiet: true; Accessible.name: Theme.tr("Done"); onClicked: root.close() }
        }
        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 5
            model: shelf.state.collections
            delegate: Rectangle {
                id: row
                required property var modelData
                width: ListView.view.width
                height: 52
                color: root.selectedId === modelData.id ? Theme.selected : Theme.elevated
                radius: 11
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 14
                    anchors.rightMargin: 6
                    Glyph { name: "folder"; width: 19; height: 19; ink: Theme.accent }
                    Text { text: row.modelData.name; color: Theme.text; Layout.fillWidth: true; elide: Text.ElideRight }
                    ActionButton { glyph: "edit"; quiet: true; Accessible.name: Theme.tr("Rename"); onClicked: { root.selectedId = row.modelData.id; nameInput.text = row.modelData.name; nameInput.forceActiveFocus() } }
                    ActionButton { glyph: "trash"; quiet: true; destructive: true; Accessible.name: Theme.tr("Delete"); onClicked: { root.deleteId = row.modelData.id; root.selectedName = row.modelData.name; confirmDelete.open() } }
                }
            }
            ScrollBar.vertical: ScrollBar {}
        }
        Text { text: Theme.tr(root.selectedId ? "Rename collection" : "New collection"); color: Theme.secondary; font.pixelSize: Theme.px(12) }
        RowLayout {
            Layout.fillWidth: true
            Field { id: nameInput; objectName: "collectionNameInput"; Layout.fillWidth: true; maximumLength: 60; placeholderText: Theme.tr("Collection name"); onAccepted: saveButton.clicked() }
            ActionButton { id: saveButton; text: Theme.tr("Save"); primary: true; onClicked: { if (shelf.saveCollection(root.selectedId, nameInput.text)) { root.selectedId = ""; nameInput.text = "" } } }
            ActionButton { visible: !!root.selectedId; glyph: "close"; quiet: true; Accessible.name: Theme.tr("Cancel"); onClicked: { root.selectedId = ""; nameInput.text = "" } }
        }
    }
    Sheet {
        id: confirmDelete
        width: Math.min(parent.width - 60, 490)
        height: 230
        z: 20
        ColumnLayout {
            anchors.fill: parent
            spacing: 18
            Text { text: Theme.tr("Delete collection?"); color: Theme.text; font.pixelSize: Theme.px(22); font.weight: Font.DemiBold }
            Text { text: Theme.tr("Delete “{name}”? Films will stay in your library.").replace("{name}", root.selectedName); color: Theme.secondary; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            RowLayout {
                Layout.alignment: Qt.AlignRight
                ActionButton { text: Theme.tr("Cancel"); onClicked: confirmDelete.close() }
                ActionButton { text: Theme.tr("Delete"); destructive: true; onClicked: { if (shelf.deleteCollection(root.deleteId)) { if (root.selectedId === root.deleteId) { root.selectedId = ""; nameInput.text = "" } confirmDelete.close() } } }
            }
        }
    }
}
