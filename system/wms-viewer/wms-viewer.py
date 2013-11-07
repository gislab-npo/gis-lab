#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author: Ivan Mincik, ivan.mincik@gmail.com
"""

import sys
import webob
import urllib
from cgi import parse_qsl
from optparse import OptionParser
from owslib.wms import WebMapService
from wsgiproxy.app import WSGIProxyApp


DEBUG=True
COMMAND_LINE_MODE=False

def _get_resolutions(scales, units, resolution=96):
	"""Helper function to compute OpenLayers resolutions."""

	resolution = float(resolution)
	factor = {'in': 1.0, 'ft': 12.0, 'mi': 63360.0,
			'm': 39.3701, 'km': 39370.1, 'dd': 4374754.0}
	
	inches = 1.0 / resolution
	monitor_l = inches / factor[units]
	
	resolutions = []
	for m in scales:
		resolutions.append(monitor_l * int(m))
	return resolutions


def page(c):
	"""Return viewer application HTML code."""

	html = ''

	c['static_url_prefix'] = 'https://rawgithub.com/imincik/gis-lab/master/system/wms-viewer/' if COMMAND_LINE_MODE else ''

	# head and javascript start
	html += """
	<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>

        <link rel="stylesheet" type="text/css" href="%(static_url_prefix)sstatic/ext-3.4.1/resources/css/ext-all.css"/>

        <script type="text/javascript" src="%(static_url_prefix)sstatic/ext-3.4.1/adapter/ext/ext-base.js"></script>
        <script type="text/javascript" src="%(static_url_prefix)sstatic/ext-3.4.1/ext-all.js"></script>

        <script type="text/javascript" src="%(static_url_prefix)sstatic/OpenLayers-2.13/OpenLayers.js"></script>
        <script type="text/javascript" src="%(static_url_prefix)sstatic/GeoExt-1.1/GeoExt.js"></script>

        <style type="text/css">
            #dpiDetection {
                height: 1in; left: -100%%; position: absolute; top: -100%%; width: 1in;
            }
            .olControlNoSelect {
                background-color:rgba(200, 200, 200, 0.3);
            }
            .legend-item .x-form-item {
                display:none;
            }
            .olControlPanPanel div {
                background-image: url("%(static_url_prefix)sstatic/images/tool-sprites.gif") !important;
                font-size: 0 !important;
                height: 15px !important;
                width: 15px !important;
            }
            .olControlZoomToMaxExtentItemInactive {
                display:none;
            }
            .olControlPanPanel .olControlPanNorthItemInactive {
                background-position: 15px -60px !important;
                left: 16px !important;
            }
            .olControlPanPanel .olControlPanSouthItemInactive {
                background-position: 15px -75px !important;
                left: 16px !important;
                top: 32px !important;
            }
            .olControlPanPanel .olControlPanWestItemInactive {
                background-position: 15px -105px !important;
                left: 2px !important;
                top: 16px !important;
            }
            .olControlPanPanel .olControlPanEastItemInactive {
                background-position: 15px -120px !important;
                left: 30px !important;
                top: 16px !important;
            }
            .olControlZoomPanel div {
                background-image: url("%(static_url_prefix)sstatic/images/tool-sprites.gif") !important;
                font-size: 0 !important;
                height: 15px !important;
                width: 15px !important;
            }
            .olControlZoomPanel .olControlZoomInItemInactive {
                background-position: 15px -240px !important;
                left: 7px !important;
                top: -5px !important;
            }
            .olControlZoomPanel .olControlZoomOutItemInactive {
                background-position: 15px -255px !important;
                left: 7px !important;
                top: 168px !important;
            }
            .x-panel-header {
                color: #15428B;
                font-family: tahoma,arial,verdana,sans-serif;
                font-size: 11px;
                font-weight: bold;
            }
            .x-panel-body-text {
                font-family: tahoma,arial,verdana,sans-serif;
                font-size: 11px;
            }
            .featureinfo-icon {
                background-image: url('%(static_url_prefix)sstatic/images/toolbar/information.png')!important;
                background: no-repeat;
            }
            .home-icon {
                background-image: url('%(static_url_prefix)sstatic/images/toolbar/home.png')!important;
                background: no-repeat;
            }
            .pan-icon {
                background-image: url('%(static_url_prefix)sstatic/images/toolbar/pan.png')!important;
                background: no-repeat;
            }
            .zoom-in-icon {
                background-image: url('%(static_url_prefix)sstatic/images/toolbar/zoom_in.png')!important;
                background: no-repeat;
            }
            .zoom-out-icon {
                background-image: url('%(static_url_prefix)sstatic/images/toolbar/zoom_out.png')!important;
                background: no-repeat;
            }
            .zoom-max-extent-icon {
                background-image: url('%(static_url_prefix)sstatic/images/toolbar/arrow_out.png')!important;
                background: no-repeat;
            }
            .previous-icon {
                background-image: url('%(static_url_prefix)sstatic/images/toolbar/arrow_left.png')!important;
                background: no-repeat;
            }
            .next-icon {
                background-image: url('%(static_url_prefix)sstatic/images/toolbar/arrow_right.png')!important;
                background: no-repeat;
            }
            .length-measure-icon {
                background-image: url('%(static_url_prefix)sstatic/images/toolbar/ruler.png')!important;
                background: no-repeat;
            }
            .area-measure-icon {
                background-image: url('%(static_url_prefix)sstatic/images/toolbar/ruler_square.png')!important;
                background: no-repeat;
            }
        </style>

        <title id="page-title">%(root_title)s</title>
        <script type="text/javascript">
	""" % c


	# configuration
	html += """function main() {
		Ext.BLANK_IMAGE_URL = "%(static_url_prefix)sstatic/images/s.gif";
		OpenLayers.DOTS_PER_INCH = %(resolution)s;
		OpenLayers.ProxyHost = "/proxy/?url=";
		var config = {
			projection: "%(projection)s",
			units: "%(units)s",
			resolutions: [%(resolutions)s],
			maxExtent: [%(extent)s],
		};

		var x = %(center_coord1)s;
		var y = %(center_coord2)s;
		var zoom = %(zoom)s;
		var layer = null;

	""" % c

	if DEBUG: html += """\tconsole.log("CONFIG: %s");\n""" % c

	# layers
	html += "\t\tvar maplayers = [];\n"
	if c['osm']:
		html += "\t\tmaplayers.push(new OpenLayers.Layer.OSM());\n"

	html += """
		var overlays_group_layer = new OpenLayers.Layer.WMS(
			"OverlaysGroup",
			["%s&TRANSPARENT=TRUE"],
			{
				layers: ["%s"],
				transparent: true,
				format: "%s",
			},
			{
				gutter: 0,
				isBaseLayer: false,
				buffer: 0,
				visibility: true,
				singleTile: true,
				// attribution: "",
			}
		);
	""" % (c['ows_url'], '", "'.join(c['layers']), 'image/png')
	html += "\tmaplayers.push(overlays_group_layer);\n"

	# map panel
	if c['osm']:
		c['allOverlays'] = 'false'
	else:
		c['allOverlays'] = 'true'
	html += """
		var mappanel = new GeoExt.MapPanel({
			region: 'center',
			title: '%(root_title)s',
			collapsible: false,
			zoom: 3,
			map: {
				allOverlays: %(allOverlays)s,
				units: config.units,
				projection: new OpenLayers.Projection(config.projection),
				resolutions: config.resolutions,
				maxExtent: new OpenLayers.Bounds(config.maxExtent[0], config.maxExtent[1],
					config.maxExtent[2], config.maxExtent[3]),
				controls: []
			},
			layers: maplayers,
			items: [{
				xtype: "gx_zoomslider",
				aggressive: true,
				vertical: true,
				height: 150,
				x: 17,
				y: 85,
				plugins: new GeoExt.ZoomSliderTip()
			}],
			tbar: [],
			bbar: []
		});
		var mappanel_container = mappanel;

		var ctrl, action;
	""" % c

	if c['has_featureinfo']:
		#featureinfo panel
		html += """
			var featureinfo_tabpanel = new Ext.TabPanel({
				id: 'featureinfo-tabpanel',
				items: [],
				listeners: {
					'tabchange': function (tabPanel, tab) {
						if (!tab) {
							return;
						}
						// deactivate features selection control on map
						//tab.selModel.selectControl.deactivate();

						var tab_layer_name = '_featureinfolayer_' + tab.title;
						Ext.each(mappanel.map.getLayersByName(new RegExp('^_featureinfolayer_.+')), function(layer) {
							layer.setVisibility(layer.name == tab_layer_name);
						});
					}
				}
			});

			var featureinfo_panel = new Ext.Panel({
				id: 'featureinfo-panel',
				title: 'Feature Info',
				layout: 'fit',
				collapsible: true,
				collapsed: true,
				height: 120,
				split: true,
				region: 'south',
				animate: false,
				items: [featureinfo_tabpanel]
			});
		"""
		html += """
			var mappanel_container = new Ext.Panel({
				layout: 'border',
				region: 'center',
				items: [
					mappanel,
					featureinfo_panel
				]
			});
		"""

		html+= """
		// Featureinfo Action
		ctrl = new OpenLayers.Control.WMSGetFeatureInfo({
			autoActivate: false,
			infoFormat: 'application/vnd.ogc.gml',
			maxFeatures: 10,
			queryVisible: true,
			clearFeaturesLayers: function() {
				featureinfo_tabpanel.removeAll(true);
				Ext.each(mappanel.map.getLayersByName(new RegExp('^_featureinfolayer_.+')), function(layer) {
					layer.destroyFeatures();
					layer.setVisibility(false);
				});
			},
			eventListeners: {
				"getfeatureinfo": function(e) {
					this.clearFeaturesLayers();
					var featureinfo_data = {};
					if (e.features.length > 0) {
						// split features by layer name
						Ext.each(e.features, function(feature) {
							var layer_name = feature.fid.split(".")[0];
							if (!featureinfo_data.hasOwnProperty(layer_name)) {
								featureinfo_data[layer_name] = [];
							}
							featureinfo_data[layer_name].push(feature);
						});

						// prepare feature attributes data for GridPanel separately for each layer
						for (var layer_name in featureinfo_data) {
							var layer_features = featureinfo_data[layer_name];

							// create vector layer for layer features if it does not already exist
							var features_layername = '_featureinfolayer_'+layer_name;
							var flayer = mappanel.map.getLayer(features_layername);
							if (flayer == null) {
								flayer = new OpenLayers.Layer.Vector(features_layername, {
									eventListeners: {},
									styleMap: new OpenLayers.StyleMap({
										'default':{
											strokeColor: '#FFCC00',
											strokeOpacity: 0.6,
											strokeWidth: 2,
											fillColor: '#FFCC00',
											fillOpacity: 0.2,
											pointRadius: 6,
										},
										'select': {
											strokeColor: '#FF0000',
											strokeOpacity: 0.8,
											strokeWidth: 2,
											fillColor: '#FF0000',
											fillOpacity: 0.7,
											pointRadius: 6,
										}
									})
								});
								flayer.id = features_layername;
								flayer.displayInLayerSwitcher = false;
							}
							mappanel.map.addLayer(flayer);

							// create header info of features attributes (of the same layer)
							var fields = [], columns = [], data = [];
							for (var attr_name in layer_features[0].attributes) {
								if (attr_name == 'geometry' || attr_name == 'boundedBy') {continue;}
								fields.push({ name: attr_name, type: 'string' });
								columns.push({id: attr_name, header: attr_name, dataIndex: attr_name});
							}

							var store = new GeoExt.data.FeatureStore({
								layer: flayer,
								fields: fields,
								features: layer_features,
								autoLoad: true
							});
							var grid_panel = new Ext.grid.GridPanel({
								title: layer_name,
								autoDestroy: true,
								store: store,
								autoHeight: true,
								viewConfig: {
									forceFit:true,
								},
								cm: new Ext.grid.ColumnModel({
									defaults: {
										sortable: false
									},
									columns: columns
								}),
								sm: new GeoExt.grid.FeatureSelectionModel({
									//autoPanMapOnSelection: true
								}),
								listeners: {
									'removed': function (grid, ownerCt ) {
										grid.selModel.unbind();
									}
								}
							});
							featureinfo_tabpanel.add(grid_panel);
						}
						featureinfo_panel.expand(false);
						featureinfo_tabpanel.setActiveTab(0);
						featureinfo_tabpanel.doLayout();
					}
				}
			}
		})
		action = new GeoExt.Action({
			control: ctrl,
			map: mappanel.map,
			cls: 'x-btn-icon',
			iconCls: 'featureinfo-icon',
			enableToggle: true,
			toggleGroup: 'featureinfo-tools',
			group: 'featureinfo-tools',
			toggleHandler: function(button, toggled) {
				if (!toggled) {
					button.baseAction.control.clearFeaturesLayers();
					featureinfo_panel.collapse(false);
				}
			},
			tooltip: 'Feature info'
		})
		mappanel.getTopToolbar().add('-', action);
		""" % c

	html += """

		//Home Action
		action = new GeoExt.Action({
			handler: function() { mappanel.map.setCenter(new OpenLayers.LonLat(%(center_coord1)s, %(center_coord2)s), %(zoom)s); },
			map: mappanel.map,
			cls: 'x-btn-icon',
			iconCls: 'home-icon',
			tooltip: 'Home'
		});
		mappanel.getTopToolbar().add('-', action);

		//Pan Map Action
		action = new GeoExt.Action({
			control: new OpenLayers.Control.MousePosition({formatOutput: function(lonLat) {return '';}}),
			map: mappanel.map,
			toggleGroup: 'tools',
			group: 'tools',
			cls: 'x-btn-icon',
			iconCls: 'pan-icon',
			tooltip: 'Pan'
		});
		mappanel.getTopToolbar().add(action);

		//Zoom In Action
		action = new GeoExt.Action({
			control: new OpenLayers.Control.ZoomBox({alwaysZoom:true}),
			map: mappanel.map,
			toggleGroup: 'tools',
			group: 'tools',
			cls: 'x-btn-icon',
			iconCls: 'zoom-in-icon',
			tooltip: 'Zoom In'
		});
		mappanel.getTopToolbar().add(action);

		//Zoom Out Action
		action = new GeoExt.Action({
			control: new OpenLayers.Control.ZoomBox({alwaysZoom:true, out:true}),
			map: mappanel.map,
			toggleGroup: 'tools',
			group: 'tools',
			cls: 'x-btn-icon',
			iconCls: 'zoom-out-icon',
			tooltip: 'Zoom Out',
		});
		mappanel.getTopToolbar().add(action);

		// Navigation history - two 'button' controls
		ctrl = new OpenLayers.Control.NavigationHistory();
		mappanel.map.addControl(ctrl);

		action = new GeoExt.Action({
			control: ctrl.previous,
			disabled: true,
			cls: 'x-btn-icon',
			iconCls: 'previous-icon',
			tooltip: 'Previous in history',
		});
		mappanel.getTopToolbar().add(action);

		action = new GeoExt.Action({
			control: ctrl.next,
			disabled: true,
			cls: 'x-btn-icon',
			iconCls: 'next-icon',
			tooltip: 'Next in history',
		});
		mappanel.getTopToolbar().add(action, '-');

		var length = new OpenLayers.Control.Measure(OpenLayers.Handler.Path, {
			immediate: true,
			persist: true,
			geodesic: true, //only for projected projections
			eventListeners: {
				measurepartial: function(evt) {
					Ext.getCmp('measurement-info').setText('Length: ' + evt.measure.toFixed(2) + evt.units);
				},
				measure: function(evt) {
					Ext.getCmp('measurement-info').setText('Length: ' + evt.measure.toFixed(2) + evt.units);
				}
			}
		});

		var area = new OpenLayers.Control.Measure(OpenLayers.Handler.Polygon, {
			immediate: true,
			persist: true,
			geodesic: true, //only for projected projections
			eventListeners: {
				measurepartial: function(evt) {
					Ext.getCmp('measurement-info').setText('Area: ' + evt.measure.toFixed(2) + evt.units + '<sup>2</sup>');
				},
				measure: function(evt) {
					Ext.getCmp('measurement-info').setText('Area: ' + evt.measure.toFixed(2) + evt.units + '<sup>2</sup>');
				}
			}
		});

		mappanel.map.addControl(length);
		mappanel.map.addControl(area);

		var length_button = new Ext.Button({
			enableToggle: true,
			toggleGroup: 'tools',
			iconCls: 'length-measure-icon',
			toggleHandler: function(button, toggled) {
				if (toggled) {
					length.activate();
				} else {
					length.deactivate();
					Ext.getCmp('measurement-info').setText('');
				}
			},
			tooltip: 'Measure length'
		});

		var area_button = new Ext.Button({
			enableToggle: true,
			toggleGroup: 'tools',
			iconCls: 'area-measure-icon',
			toggleHandler: function(button, toggled) {
				if (toggled) {
					area.activate();
				} else {
					area.deactivate();
					Ext.getCmp('measurement-info').setText('');
				}
			},
			tooltip: 'Measure area'
		});
		mappanel.getTopToolbar().add(length_button, area_button);
	""" % c

	# tree node
	html += """
			var layers_root = new Ext.tree.TreeNode({
				text: 'Layers',
				expanded: true,
				draggable: false
			});
	"""

	# base layers tree
	if c['osm']:
		html += """
			layers_root.appendChild(new GeoExt.tree.BaseLayerContainer({
				text: 'Base Layers',
				map: mappanel.map,
				leaf: false,
				expanded: true,
				draggable: false,
				isTarget: false,
				split: true
			}));
		"""

	# overlay layers tree
	html += """
			layers_root.appendChild(new GeoExt.tree.LayerNode({
				text: 'Overlays',
				layer: overlays_group_layer,
				leaf: false,
				expanded: true,
				loader: {
					param: "LAYERS"
				}
			}));
	"""

	# layers tree
	html += """
			var layer_treepanel = new Ext.tree.TreePanel({
				title: 'Content',
				enableDD: true,
				root: layers_root,
				split: true,
				border: true,
				collapsible: false,
				cmargins: '0 0 0 0',
				autoScroll: true
			});
	"""

	# legend
	html += """
		var layer_legend = new GeoExt.LegendPanel({
			title: 'Legend',
			map: mappanel.map,
			border: false,
			ascending: false,
			autoScroll: true,
			filter: function(record){
				if (record.data.title == 'POINTS') {
					return false;
				}
				return true;
			},
			defaults: {
				cls: 'legend-item',
				baseParams: {
					FORMAT: 'image/png',
					SYMBOLHEIGHT: '2',
					SYMBOLWIDTH: '4',
					LAYERFONTSIZE: '8',
					LAYERFONTBOLD: 'true',
					ITEMFONTSIZE: '8',
					ICONLABELSPACE: '15'
				}
			}
		});
	"""

	# properties
	html += """
			var properties = new Ext.Panel({
				title: 'Properties',
				autoScroll: true,
				html: '<div class="x-panel-body-text"><p><b>Author: </b>%(author)s</p><p><b>E-mail: </b>%(email)s</p><p><b>Organization: </b>%(organization)s</p><b>Abstract: </b>%(abstract)s</p></div>'
			});
	""" % c

	# legend and properties accordion panel
	html += """
			var accordion = new Ext.Panel({
				layout: {
					type: 'accordion',
					titleCollapse: true,
					animate: false,
					activeOnTop: false
				},
				items: [
					layer_legend,
					properties
				]
			});
	"""

	# left panel
	html += """
			var left_panel = new Ext.Panel({
				region: 'west',
				width: 200,
				defaults: {
					width: '100%',
					flex: 1
				},
				layout: 'vbox',
				collapsible: true,
				layoutConfig: {
					align: 'stretch',
					pack: 'start'
				},
				items: [
					layer_treepanel,
					accordion
				]
			});
	"""

	# viewport
	html += """
			var webgis = new Ext.Viewport({
				layout: "border",
				items: [
					mappanel_container,
					left_panel
				]
			});
	"""

	# controls
	html += """
			Ext.namespace("GeoExt.Toolbar");

			GeoExt.Toolbar.ControlDisplay = Ext.extend(Ext.Toolbar.TextItem, {

				control: null,
				map: null,

				onRender: function(ct, position) {
					this.text = this.text ? this.text : '&nbsp;';

					GeoExt.Toolbar.ControlDisplay.superclass.onRender.call(this, ct, position);
					this.control.div = this.el.dom;

					if (!this.control.map && this.map) {
						this.map.addControl(this.control);
					}
				}
			});
			var coords = new GeoExt.Toolbar.ControlDisplay({control: new OpenLayers.Control.MousePosition({separator: ' , '}), map: mappanel.map});

			mappanel.getBottomToolbar().add(new Ext.Toolbar.TextItem({text: config.projection}));
			mappanel.getBottomToolbar().add(' ', '-', '');
			mappanel.getBottomToolbar().add(coords);
			var measurement_output = new Ext.Toolbar.TextItem({
				id:'measurement-info',
				text: ''
			});
			mappanel.getBottomToolbar().add(' ', '-', ' ', measurement_output);

			mappanel.map.setCenter(new OpenLayers.LonLat(%(center_coord1)s, %(center_coord2)s), %(zoom)s);
			mappanel.map.addControl(new OpenLayers.Control.Scale());
			mappanel.map.addControl(new OpenLayers.Control.ScaleLine());
			mappanel.map.addControl(new OpenLayers.Control.PanPanel());
			mappanel.map.addControl(new OpenLayers.Control.ZoomPanel());
			mappanel.map.addControl(new OpenLayers.Control.Navigation());
			mappanel.map.addControl(new OpenLayers.Control.Attribution());
	""" % c

	# POI markers
	if 'pois' in c:
		html += """
			var markers = new OpenLayers.Layer.Vector('POINTS', {
				styleMap: new OpenLayers.StyleMap({
					'default':{
						label: '${label}',
						fontSize: '12px',
						fontWeight: 'bold',
						labelAlign: 'lb',
						strokeColor: '#000000',
						strokeOpacity: 1,
						strokeWidth: 0.5,
						fillColor: '#FF0000',
						fillOpacity: 0.8,
						pointRadius: 6,
						labelYOffset: '6',
						labelXOffset: '6',
						fontColor: 'red',
					}
				})
			});
			mappanel.map.addLayer(markers);
		"""
		for coord1, coord2, text in c['pois']:
			html += """
				// create a point feature
				var point = new OpenLayers.Geometry.Point({0}, {1});
				var poi_feature = new OpenLayers.Feature.Vector(point);
				poi_feature.attributes = {{
					label: "{2}"
				}};
				markers.addFeatures(poi_feature);
			""".format(coord1, coord2, text)

	html += """
		}; // end of main function
	"""
	html += """
		Ext.QuickTips.init();
		Ext.onReady(main);
				</script>
			</head>
			<body>
				<div id="overviewLegend" style="margin-left:10px"></div>
				<div id="dpiDetection"></div>
			</body>
		</html>
	"""

	return html


def application(environ, start_response):
	"""Return server response."""

	if environ["PATH_INFO"].startswith("/proxy/"):
		url = environ['QUERY_STRING'].replace("url=", "")
		url = urllib.unquote(url)
		req = webob.Request.blank(url)
		req.environ["REMOTE_ADDR"] = ""
		resp = req.get_response(WSGIProxyApp(req.host_url))
		return resp(req.environ, start_response)

	OWS_URL="http://192.168.50.5/cgi-bin/qgis_mapserv.fcgi" #  TODO: do not hardcode this
	DEFAULT_SCALES="1000000,500000,250000,100000,50000,25000,10000,5000,2500,1000,500"
	PROJECTION_UNITS_DD=('EPSG:4326',)

	qs = dict(parse_qsl(environ['QUERY_STRING'])) # collect GET parameters
	qs = dict((k.upper(), v) for k, v in qs.iteritems()) # change GET parameters names to uppercase

	try:
		projectfile = '/storage/share/' + qs.get('PROJECT') # TODO: use Apache rewrite
		getcapabilities_url = "{0}/?map={1}&REQUEST=GetCapabilities".format(OWS_URL, projectfile)

		wms_service = WebMapService(getcapabilities_url, version="1.1.1") # read WMS GetCapabilities
	except:
		start_response('404 NOT FOUND', [('content-type', 'text/plain')])
		return ('Project file does not exist or it is not accessible.',)

	root_layer = None
	for layer in wms_service.contents.itervalues():
		if not layer.parent:
			root_layer = layer
			break
	if not root_layer: raise Exception("Root layer not found.")

	extent = root_layer.boundingBox[:-1]

	# set some parameters from GET request (can override parameters from WMS GetCapabilities)
	if qs.get('DPI'):
		resolution = qs.get('DPI')
	else:
		resolution = 96

	if qs.get('SCALES'):
		scales = map(int, qs.get('SCALES').split(","))
	else:
		scales = map(int, DEFAULT_SCALES.split(","))

	if qs.get('ZOOM'):
		zoom = qs.get('ZOOM')
	else:
		zoom = 0

	if qs.get('CENTER'):
		center_coord1 = qs.get('CENTER').split(',')[0]
		center_coord2 = qs.get('CENTER').split(',')[1]
	else:
		center_coord1 = (extent[0]+extent[2])/2.0
		center_coord2 = (extent[1]+extent[3])/2.0


	if qs.get('LAYERS'):
		layers_names = qs.get('LAYERS').split(',')
	else:
		layers_names = [layer.name.encode('UTF-8') for layer in root_layer.layers][::-1]

	c = {} # configuration dictionary which will be used in HTML template
	c['projectfile'] = projectfile
	c['projection'] = root_layer.boundingBox[-1]

	if c['projection'] in PROJECTION_UNITS_DD: # TODO: this is very naive
		c['units'] = 'dd'
	else:
		c['units'] = 'm'

	if qs.get('OSM') in ('true', 'TRUE', 'True') and c['projection'] == 'EPSG:3857':
		c['osm'] = True
	else:
		c['osm'] = False

	if qs.get('POINTS'):
		points_data = qs.get('POINTS')
		c['pois'] = []
		for point_data in points_data.split("|"):
			coord1, coord2, text = point_data.split(",")
			c['pois'].append((coord1, coord2, text))

	c['resolution'] = resolution
	c['extent'] = ",".join(map(str, extent))
	c['center_coord1'] = center_coord1
	c['center_coord2'] = center_coord2
	c['scales'] = scales
	c['zoom'] = zoom
	c['resolutions'] = ', '.join(str(r) for r in _get_resolutions(c['scales'], c['units'], c['resolution']))
	c['author'] = wms_service.provider.contact.name.encode('UTF-8') if wms_service.provider.contact.name else ''
	c['email'] = wms_service.provider.contact.email.encode('UTF-8') if wms_service.provider.contact.email else ''
	c['organization'] = wms_service.provider.contact.organization.encode('UTF-8') if wms_service.provider.contact.organization else ''
	c['abstract'] = wms_service.identification.abstract.encode('UTF-8') if wms_service.identification.abstract else ''

	c['root_layer'] = root_layer.name.encode('UTF-8')
	c['root_title'] = wms_service.identification.title.encode('UTF-8')
	c['layers'] = layers_names
	c['ows_url'] = '{0}/?map={1}&DPI={2}'.format(OWS_URL, projectfile, resolution)
	c['ows_get_capabilities_url'] = getcapabilities_url

	has_featureinfo = False
	for operation in wms_service.operations:
		if operation.name == 'GetFeatureInfo':
			has_featureinfo = 'application/vnd.ogc.gml' in operation.formatOptions
			break
	c['has_featureinfo'] = has_featureinfo

	start_response('200 OK', [('Content-type','text/html')])
	return page(c)


def run(port=9997):
	"""Start WSGI server."""

	from wsgiref import simple_server
	httpd = simple_server.WSGIServer(('', port), simple_server.WSGIRequestHandler,)
	httpd.set_app(application)
	try:
		print "Starting server. Point your web browser to 'http://127.0.0.1:%s'." % port
		httpd.serve_forever()
	except KeyboardInterrupt:
		print "Shutting down server."
		sys.exit(0)


if __name__ == "__main__":
	parser = OptionParser()

	parser.add_option("-p", "--port", help="port to run server on [optional]",
		dest="port", action='store', type="int", default=9991)

	options, args = parser.parse_args()
	COMMAND_LINE_MODE = True
	run(options.port)


# vim: set ts=4 sts=4 sw=4 noet:
