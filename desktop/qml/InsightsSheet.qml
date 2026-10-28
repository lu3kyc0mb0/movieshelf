import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Sheet {
    id: root
    objectName: "insightsSheet"
    width: Math.min(parent.width - 48, 940)
    height: Math.min(parent.height - 48, 720)
    property string scopeId: ""
    property var report: ({movies: 0, totalViews: 0, rewatches: 0, undatedWatched: 0, rated: 0, unrated: 0, averageRating: "—", months: [], maxMonth: 0, ratings: [], maxRating: 0})
    property var scopes: [{id: "", name: Theme.tr("All movies")}].concat(shelf.state.collections.map(item => ({id: item.id, name: item.name})))
    function refresh() { report = shelf.collectionInsights(scopeId) }
    onOpened: {
        scopeId = shelf.state.view.startsWith("collection:") ? shelf.state.view.slice(11) : ""
        let found = scopes.findIndex(item => item.id === scopeId)
        scopeChoice.currentIndex = found < 0 ? 0 : found
        refresh()
    }
    ColumnLayout {
        anchors.fill: parent
        spacing: 18
        RowLayout {
            Layout.fillWidth: true
            Text { text: Theme.tr("Collection insights"); color: Theme.text; font.pixelSize: 25; font.weight: Font.DemiBold; Layout.fillWidth: true }
            ActionButton { glyph: "close"; quiet: true; Accessible.name: Theme.tr("Done"); onClicked: root.close() }
        }
        RowLayout {
            Layout.fillWidth: true
            Text { text: Theme.tr("Collection"); color: Theme.secondary; font.pixelSize: 13 }
            Choice { id: scopeChoice; objectName: "insightsScope"; Layout.preferredWidth: 250; model: root.scopes.map(item => item.name); onActivated: { root.scopeId = root.scopes[currentIndex].id; root.refresh() } }
            Item { Layout.fillWidth: true }
            Text { text: Theme.tr("Based on your saved movies and watch dates"); color: Theme.secondary; font.pixelSize: 12 }
        }
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth
            ColumnLayout {
                width: parent.width
                spacing: 22
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    Repeater {
                        model: [
                            {value: root.report.movies, label: "Movies"},
                            {value: root.report.totalViews, label: "Dated views"},
                            {value: root.report.rewatches, label: "Rewatches"},
                            {value: root.report.averageRating, label: "Average rating"}
                        ]
                        delegate: Rectangle {
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredHeight: 82
                            radius: 13
                            color: Theme.elevated
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 13
                                spacing: 4
                                Text { text: modelData.value; color: Theme.text; font.pixelSize: 21; font.weight: Font.DemiBold }
                                Text { text: Theme.tr(modelData.label); color: Theme.secondary; font.pixelSize: 11 }
                            }
                        }
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Text { text: Theme.tr("Viewing trend · last 12 months"); color: Theme.text; font.pixelSize: 17; font.weight: Font.DemiBold }
                    Text { text: Theme.tr("Each bar counts recorded watch dates. Gold shows repeat watches."); color: Theme.secondary; font.pixelSize: 12 }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 180
                        radius: 13
                        color: Theme.elevated
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 15
                            spacing: 5
                            Repeater {
                                model: root.report.months
                                delegate: ColumnLayout {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    spacing: 5
                                    Text { text: modelData.count ? modelData.count : ""; color: Theme.text; font.pixelSize: 11; Layout.alignment: Qt.AlignHCenter }
                                    Item {
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        Rectangle {
                                            anchors.bottom: parent.bottom
                                            anchors.horizontalCenter: parent.horizontalCenter
                                            width: Math.min(parent.width - 4, 30)
                                            height: root.report.maxMonth ? parent.height * modelData.count / root.report.maxMonth : 0
                                            radius: 5
                                            color: Theme.accent
                                            Behavior on height { NumberAnimation { duration: Theme.duration; easing.type: Easing.OutCubic } }
                                            Rectangle {
                                                anchors.bottom: parent.bottom
                                                width: parent.width
                                                height: modelData.count ? parent.height * modelData.rewatches / modelData.count : 0
                                                radius: 5
                                                color: Theme.gold
                                            }
                                        }
                                    }
                                    Text { text: modelData.label.slice(5) + "/" + modelData.label.slice(2, 4); color: Theme.secondary; font.pixelSize: 10; Layout.alignment: Qt.AlignHCenter }
                                }
                            }
                        }
                    }
                    Text { visible: root.report.undatedWatched > 0; text: Theme.tr("Watched films without a recorded date: ") + root.report.undatedWatched; color: Theme.secondary; font.pixelSize: 12 }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Text { text: Theme.tr("Your rating distribution"); color: Theme.text; font.pixelSize: 17; font.weight: Font.DemiBold }
                    Text { text: Theme.tr("Rated films: ") + root.report.rated + "  ·  " + Theme.tr("Unrated films: ") + root.report.unrated; color: Theme.secondary; font.pixelSize: 12 }
                    Repeater {
                        model: root.report.ratings
                        delegate: RowLayout {
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredHeight: 24
                            spacing: 12
                            Text { text: modelData.rating; color: Theme.secondary; font.pixelSize: 12; Layout.preferredWidth: 18; horizontalAlignment: Text.AlignRight }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 13
                                radius: 6
                                color: Theme.elevated
                                Rectangle {
                                    width: root.report.maxRating ? parent.width * modelData.count / root.report.maxRating : 0
                                    height: parent.height
                                    radius: 6
                                    color: Theme.accent
                                    Behavior on width { NumberAnimation { duration: Theme.duration; easing.type: Easing.OutCubic } }
                                }
                            }
                            Text { text: modelData.count; color: Theme.text; font.pixelSize: 12; Layout.preferredWidth: 24; horizontalAlignment: Text.AlignRight }
                        }
                    }
                }
            }
        }
    }
}
