# -*- coding: utf-8 -*-
"""
/***************************************************************************
 NewRaptor
                                 A QGIS plugin
 Add a new raptor nest, create buffer and impacte table
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-10-01
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Josep Andreu Sabaté
        email                : josep.andreu@e-campus.uab.cat
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QDate
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction,  QMessageBox, QTableWidgetItem

from qgis.core import QgsProject, QgsFeature, QgsGeometry, QgsPoint
# Initialize Qt resources from file resources.py
from .resources import *

# Import the code for the dialog
from .new_raptor_dialog import NewRaptorDialog
from .impact_table import DlgTable
import os.path


class NewRaptor:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'NewRaptor_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Add New Raptor')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('NewRaptor', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/new_raptor/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Add New Raptor Nest'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&Add New Raptor'),
                action)
            self.iface.removeToolBarIcon(action)


    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = NewRaptorDialog()
            self.dlg.cmbSpecies.currentTextChanged.connect(self.evt_cmbSpecies_changed)
            # self.dlg en comptes de self pk ens referim a dialog no a la classe NewRaptor

        # QMessageBox.information(self.dlg, "Message", "Should run every time")
        mc = self.iface.mapCanvas()
        self.dlg.spbLatitude.setValue(mc.center().y())
        self.dlg.spbLongitude.setValue(mc.center().x())
        self.dlg.dteLast.setDate(QDate.currentDate())

        # input
        map_layers = []
        for lyr in mc.layers():
            map_layers.append(lyr.name())
        #QMessageBox.information(self.dlg, "Layers", str(map_layers))
        missing_layers = []
        if not "Raptor Nests" in map_layers:
            missing_layers.append("Raptor Nests")
        if not "Raptor Buffer" in map_layers:
            missing_layers.append("Raptor Buffer")
        if not "Linear Buffer" in map_layers:
            missing_layers.append("Linear Buffer")
        if missing_layers:
            msg = "The following layers are missing from this project\n"
            for lyr in missing_layers:
                msg += "\n{}".format(lyr)
            QMessageBox.critical(self.dlg, "Missing layers", msg)
            return # return stop the executing if there are missing layers




        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            QMessageBox.information(self.dlg, "Message", "Should only run if OK button is clicked")
            lyrNests = QgsProject.instance().mapLayersByName("Raptor Nests")[0]
            lyrBuffer = QgsProject.instance().mapLayersByName("Raptor Buffer")[0]
            lyrLinear  = QgsProject.instance().mapLayersByName("Linear Buffer")[0]
            idxNestID = lyrNests.fields().indexOf("Nest_ID")
            valNestID = lyrNests.maximumValue(idxNestID) +1
            valLat = self.dlg.spbLatitude.value()
            valLng = self.dlg.spbLongitude.value()
            valSpecies = self.dlg.cmbSpecies.currentText()  # cmb from combobox
            valBuffer = self.dlg.spbBuffer.value()
            valStatus = self.dlg.cmbStatus.currentText()
            valLast = self.dlg.dteLast.date()
            QMessageBox.information(self.dlg, "Message", "New Nest ID: {}\n\n Latitude: {}\nLongitude: {}\nSpecies: {}\nBuffer: {}\nStatus: {}\n Last Survey: {}".format(valNestID,valLat, valLng, valSpecies, valBuffer, valStatus, valLast))
            # creating a feature with attributes and geometries
            ftrNest = QgsFeature(lyrNests.fields())
            ftrNest.setAttribute("lat_y_dd", valLat)
            ftrNest.setAttribute("long_x_dd", valLng)
            ftrNest.setAttribute("recentspec", valSpecies)
            ftrNest.setAttribute("buf_dist", valBuffer)
            ftrNest.setAttribute("recentstat", valStatus)
            ftrNest.setAttribute("lastsurvey", valLast)
            ftrNest.setAttribute("Nest_ID", valNestID)
            geom = QgsGeometry(QgsPoint(valLng, valLat))
            ftrNest.setGeometry(geom)
            pr = lyrNests.dataProvider()
            pr.addFeatures([ftrNest])
            lyrNests.reload()

            pr = lyrBuffer.dataProvider()
            buffer = geom.buffer(valBuffer, 10)
            ftrNest.setGeometry(buffer)
            pr.addFeatures([ftrNest])
            lyrBuffer.reload()

            dlgTable = DlgTable()
            dlgTable.setWindowTitle("Impacts Table for Nest {}".format(valNestID))
            # Find linear projects that will be impacted and report them  in the table
            # intersects
            bb = buffer.boundingBox() # bc we want check instersect only inside boundingbox not all map
            linears = lyrLinear.getFeatures(bb) # bb bounding box rectangle
            for linear in linears:
                valID = linear.attribute("Project")
                valType = linear.attribute("type")
                valDistance = linear.geometry().distance(geom)
                if valDistance < valBuffer:
                    # Populate table with linear data
                    row = dlgTable.tableimpacts.rowCount()
                    dlgTable.tableimpacts.insertRow(row)
                    dlgTable.tableimpacts.setItem(row, 0, QTableWidgetItem(str(valID)))
                    dlgTable.tableimpacts.setItem(row, 1, QTableWidgetItem(valType))
                    dlgTable.tableimpacts.setItem(row, 2, QTableWidgetItem("{:4.5f}".format(valDistance))) # 5 decimals


            dlgTable.show()
            dlgTable.exec_()

        else:
            QMessageBox.information(self.dlg, "Message", "Should only run if cancelled")

    def evt_cmbSpecies_changed(self, species):
        if species == "Swainsons Hawk":
            self.dlg.spbBuffer.setValue(0.004)
        else:
            self.dlg.spbBuffer.setValue(0.008)