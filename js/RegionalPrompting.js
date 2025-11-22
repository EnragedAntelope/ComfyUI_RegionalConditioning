// Enhanced Regional Prompting with Inline Text Inputs
// Created: 2025-11-22
// All-in-one nodes with CLIP input and prompt boxes

import { app } from "/scripts/app.js";
import {CUSTOM_INT, transformFunc, swapInputs, renameNodeInputs, removeNodeInputs, getDrawColor, computeCanvasSize} from "./utils.js"

// Shared canvas function for both enhanced nodes
function addRegionalPrompterCanvas(node, app) {

	const widget = {
		type: "customCanvas",
		name: "RegionalPrompter-Canvas",
		get value() {
			return this.canvas.value;
		},
		set value(x) {
			this.canvas.value = x;
		},
		draw: function (ctx, node, widgetWidth, widgetY) {

			if (!node.canvasHeight) {
				computeCanvasSize(node, node.size)
			}

			const visible = true
			const t = ctx.getTransform();
			const margin = 10
			const border = 2

			const widgetHeight = node.canvasHeight
			const values = node.properties["values"]
			const width = Math.round(node.properties["width"])
			const height = Math.round(node.properties["height"])

			const scale = Math.min((widgetWidth-margin*2)/width, (widgetHeight-margin*2)/height)

			// Find index widget (it's after CLIP and prompt inputs)
			let indexWidget = null;
			for (let i = 0; i < node.widgets.length; i++) {
				if (node.widgets[i].name === "index") {
					indexWidget = node.widgets[i];
					break;
				}
			}
			const index = indexWidget ? Math.round(indexWidget.value) : 0;

			Object.assign(this.canvas.style, {
				left: `${t.e}px`,
				top: `${t.f + (widgetY*t.d)}px`,
				width: `${widgetWidth * t.a}px`,
				height: `${widgetHeight * t.d}px`,
				position: "absolute",
				zIndex: 1,
				fontSize: `${t.d * 10.0}px`,
				pointerEvents: "none",
			});

			this.canvas.hidden = !visible;

			let backgroundWidth = width * scale
			let backgroundHeight = height * scale

			let xOffset = margin
			if (backgroundWidth < widgetWidth) {
				xOffset += (widgetWidth-backgroundWidth)/2 - margin
			}
			let yOffset = margin
			if (backgroundHeight < widgetHeight) {
				yOffset += (widgetHeight-backgroundHeight)/2 - margin
			}

			let widgetX = xOffset
			widgetY = widgetY + yOffset

			ctx.fillStyle = "#000000"
			ctx.fillRect(widgetX-border, widgetY-border, backgroundWidth+border*2, backgroundHeight+border*2)

			ctx.fillStyle = globalThis.LiteGraph.NODE_DEFAULT_BGCOLOR
			ctx.fillRect(widgetX, widgetY, backgroundWidth, backgroundHeight);

			function getDrawArea(v) {
				let x = v[0]*backgroundWidth/width
				let y = v[1]*backgroundHeight/height
				let w = v[2]*backgroundWidth/width
				let h = v[3]*backgroundHeight/height

				if (x > backgroundWidth) { x = backgroundWidth}
				if (y > backgroundHeight) { y = backgroundHeight}

				if (x+w > backgroundWidth) {
					w = Math.max(0, backgroundWidth-x)
				}

				if (y+h > backgroundHeight) {
					h = Math.max(0, backgroundHeight-y)
				}

				return [x, y, w, h]
			}

			// Draw all the conditioning zones
			for (const [k, v] of values.entries()) {

				if (k == index) {continue}

				const [x, y, w, h] = getDrawArea(v)

				ctx.fillStyle = getDrawColor(k/values.length, "80")
				ctx.fillRect(widgetX+x, widgetY+y, w, h)

			}

			ctx.beginPath();
			ctx.lineWidth = 1;

			for (let x = 0; x <= width/64; x += 1) {
				ctx.moveTo(widgetX+x*64*scale, widgetY);
				ctx.lineTo(widgetX+x*64*scale, widgetY+backgroundHeight);
			}

			for (let y = 0; y <= height/64; y += 1) {
				ctx.moveTo(widgetX, widgetY+y*64*scale);
				ctx.lineTo(widgetX+backgroundWidth, widgetY+y*64*scale);
			}

			ctx.strokeStyle = "#00000050";
			ctx.stroke();
			ctx.closePath();

			// Draw currently selected zone
			let [x, y, w, h] = getDrawArea(values[index])

			w = Math.max(32*scale, w)
			h = Math.max(32*scale, h)

			ctx.fillStyle = "#ffffff"
			ctx.fillRect(widgetX+x, widgetY+y, w, h)

			const selectedColor = getDrawColor(index/values.length, "FF")
			ctx.fillStyle = selectedColor
			ctx.fillRect(widgetX+x+border, widgetY+y+border, w-border*2, h-border*2)

			ctx.lineWidth = 1;
			ctx.closePath();

		},
	};

	widget.canvas = document.createElement("canvas");
	widget.canvas.className = "dave-custom-canvas";

	widget.parent = node;
	document.body.appendChild(widget.canvas);

	node.addCustomWidget(widget);

	app.canvas.onDrawBackground = function () {
		for (let n in app.graph._nodes) {
			n = app.graph._nodes[n];
			for (let w in n.widgets) {
				let wid = n.widgets[w];
				if (Object.hasOwn(wid, "canvas")) {
					wid.canvas.style.left = -8000 + "px";
					wid.canvas.style.position = "absolute";
				}
			}
		}
	};

	node.onResize = function (size) {
		computeCanvasSize(node, size);
	}

	return { minWidth: 200, minHeight: 200, widget }
}

app.registerExtension({
	name: "Comfy.Davemane42.RegionalPrompterSimple",
	async beforeRegisterNodeDef(nodeType, nodeData, app) {
		if (nodeData.name === "RegionalPrompterSimple") {
			const onNodeCreated = nodeType.prototype.onNodeCreated;
			nodeType.prototype.onNodeCreated = function () {
				const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

				this.setProperty("width", 512)
				this.setProperty("height", 512)
				// Default template: Two example boxes pre-drawn
				// Region 1 (red sports car): left side, 200x250px starting at (50, 150)
				// Region 2 (street vendor): right side, 180x250px starting at (280, 150)
				this.setProperty("values", [
					[50, 150, 200, 250, 1.0],   // Region 1
					[280, 150, 180, 250, 1.0]    // Region 2
				])

				this.selected = false

				this.serialize_widgets = true;

				// Add canvas after the prompt inputs
				addRegionalPrompterCanvas(this, app)

				// Find where index widget should be inserted (after canvas)
				const indexWidgetStartPos = this.widgets.length;
				this.index = indexWidgetStartPos;

				CUSTOM_INT(
					this,
					"index",
					0,
					function (v, _, node) {
						let values = node.properties["values"]

						// Widget indices are after canvas and index
						const offset = indexWidgetStartPos + 1;
						if (node.widgets.length > offset + 4) {
							node.widgets[offset].value = values[v][0]
							node.widgets[offset + 1].value = values[v][1]
							node.widgets[offset + 2].value = values[v][2]
							node.widgets[offset + 3].value = values[v][3]
							if (!values[v][4]) {values[v][4] = 1.0}
							node.widgets[offset + 4].value = values[v][4]
						}
					},
					{ step: 10, max: 1 }
				)

				CUSTOM_INT(this, "x", 0, function (v, _, node) {transformFunc(this, v, node, 0)})
				CUSTOM_INT(this, "y", 0, function (v, _, node) {transformFunc(this, v, node, 1)})
				CUSTOM_INT(this, "width", 0, function (v, _, node) {transformFunc(this, v, node, 2)})
				CUSTOM_INT(this, "height", 0, function (v, _, node) {transformFunc(this, v, node, 3)})
				CUSTOM_INT(this, "strength", 1, function (v, _, node) {transformFunc(this, v, node, 4)}, {"min": 0.0, "max": 10.0, "step": 0.1, "precision": 2})

				this.onRemoved = function () {
					for (let y in this.widgets) {
						if (this.widgets[y].canvas) {
							this.widgets[y].canvas.remove();
						}
					}
				};

				this.onSelected = function () {
					this.selected = true
				}
				this.onDeselected = function () {
					this.selected = false
				}

				return r;
			};
		}
	},
	loadedGraphNode(node, _) {
		if (node.type === "RegionalPrompterSimple") {
			node.widgets[node.index].options["max"] = node.properties["values"].length-1
		}
	},

});

app.registerExtension({
	name: "Comfy.Davemane42.RegionalPrompterFlux",
	async beforeRegisterNodeDef(nodeType, nodeData, app) {
		if (nodeData.name === "RegionalPrompterFlux") {
			const onNodeCreated = nodeType.prototype.onNodeCreated;
			nodeType.prototype.onNodeCreated = function () {
				const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

				this.setProperty("width", 1024)
				this.setProperty("height", 1024)
				// Default template: Two example boxes pre-drawn
				// Region 1 (red sports car): left side, 400x500px starting at (100, 300)
				// Region 2 (street vendor): right side, 350x500px starting at (560, 300)
				this.setProperty("values", [
					[100, 300, 400, 500, 1.0],   // Region 1
					[560, 300, 350, 500, 1.0]    // Region 2
				])

				this.selected = false

				this.serialize_widgets = true;

				// Add canvas after the prompt inputs
				addRegionalPrompterCanvas(this, app)

				// Find where index widget should be inserted (after canvas)
				const indexWidgetStartPos = this.widgets.length;
				this.index = indexWidgetStartPos;

				CUSTOM_INT(
					this,
					"index",
					0,
					function (v, _, node) {
						let values = node.properties["values"]

						// Widget indices are after canvas and index
						const offset = indexWidgetStartPos + 1;
						if (node.widgets.length > offset + 4) {
							node.widgets[offset].value = values[v][0]
							node.widgets[offset + 1].value = values[v][1]
							node.widgets[offset + 2].value = values[v][2]
							node.widgets[offset + 3].value = values[v][3]
							if (!values[v][4]) {values[v][4] = 1.0}
							node.widgets[offset + 4].value = values[v][4]
						}
					},
					{ step: 10, max: 1 }
				)

				CUSTOM_INT(this, "x", 0, function (v, _, node) {transformFunc(this, v, node, 0)})
				CUSTOM_INT(this, "y", 0, function (v, _, node) {transformFunc(this, v, node, 1)})
				CUSTOM_INT(this, "width", 0, function (v, _, node) {transformFunc(this, v, node, 2)})
				CUSTOM_INT(this, "height", 0, function (v, _, node) {transformFunc(this, v, node, 3)})
				CUSTOM_INT(this, "strength", 1, function (v, _, node) {transformFunc(this, v, node, 4)}, {"min": 0.0, "max": 10.0, "step": 0.1, "precision": 2})

				this.onRemoved = function () {
					for (let y in this.widgets) {
						if (this.widgets[y].canvas) {
							this.widgets[y].canvas.remove();
						}
					}
				};

				this.onSelected = function () {
					this.selected = true
				}
				this.onDeselected = function () {
					this.selected = false
				}

				// Dynamic canvas sync: Watch width/height widgets and update canvas properties
				// Find width and height widgets (they're created from INPUT_TYPES)
				const widthWidget = this.widgets.find(w => w.name === "width");
				const heightWidget = this.widgets.find(w => w.name === "height");

				if (widthWidget) {
					const originalWidthCallback = widthWidget.callback;
					widthWidget.callback = function(value) {
						// Update canvas property to match
						this.properties["width"] = value;
						// Call original callback if it exists
						if (originalWidthCallback) {
							originalWidthCallback.apply(this, arguments);
						}
					}.bind(this);
				}

				if (heightWidget) {
					const originalHeightCallback = heightWidget.callback;
					heightWidget.callback = function(value) {
						// Update canvas property to match
						this.properties["height"] = value;
						// Call original callback if it exists
						if (originalHeightCallback) {
							originalHeightCallback.apply(this, arguments);
						}
					}.bind(this);
				}

				return r;
			};
		}
	},
	loadedGraphNode(node, _) {
		if (node.type === "RegionalPrompterFlux") {
			node.widgets[node.index].options["max"] = node.properties["values"].length-1

			// Sync canvas properties with widget values on load
			const widthWidget = node.widgets.find(w => w.name === "width");
			const heightWidget = node.widgets.find(w => w.name === "height");
			if (widthWidget) {
				node.properties["width"] = widthWidget.value;
			}
			if (heightWidget) {
				node.properties["height"] = heightWidget.value;
			}
		}
	},

});
