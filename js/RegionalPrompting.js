// Enhanced Regional Prompting with Inline Text Inputs
// Created: 2025-11-22
// All-in-one nodes with CLIP input and prompt boxes

import { app } from "/scripts/app.js";
import {CUSTOM_INT, transformFunc, swapInputs, renameNodeInputs, removeNodeInputs, getDrawColor, computeCanvasSize, calculateDefaultRegions} from "./utils.js"

// Shared canvas function for both enhanced nodes
function addEasyRegionCanvas(node, app) {

	const widget = {
		type: "customCanvas",
		name: "EasyRegion-Canvas",
		value: {},
		computeSize: function(width) {
			// Tell LiteGraph this widget needs 280px of height
			return [width, 280];
		},
		draw: function (ctx, node, widgetWidth, widgetY) {

			if (!node.canvasHeight) {
				computeCanvasSize(node, node.size)
			}

			const margin = 10
			const border = 2

			const widgetHeight = node.canvasHeight || 280
			const values = node.properties["values"] || []
			const width = Math.round(node.properties["width"] || 512)
			const height = Math.round(node.properties["height"] || 512)

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

				// Add region label
				ctx.fillStyle = "#ffffff";
				ctx.font = "bold 14px Arial";
				ctx.textAlign = "left";
				ctx.fillText(`Region ${k+1}`, widgetX+x+5, widgetY+y+18);

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

			// Draw currently selected zone (if values exist)
			if (values.length > 0 && index < values.length) {
				let [x, y, w, h] = getDrawArea(values[index])

				w = Math.max(32*scale, w)
				h = Math.max(32*scale, h)

				ctx.fillStyle = "#ffffff"
				ctx.fillRect(widgetX+x, widgetY+y, w, h)

				const selectedColor = getDrawColor(index/values.length, "FF")
				ctx.fillStyle = selectedColor
				ctx.fillRect(widgetX+x+border, widgetY+y+border, w-border*2, h-border*2)

				// Add label to selected region too
				ctx.fillStyle = "#ffffff";
				ctx.font = "bold 14px Arial";
				ctx.textAlign = "left";
				ctx.fillText(`Region ${index+1}`, widgetX+x+5, widgetY+y+18);

				ctx.lineWidth = 1;
				ctx.closePath();
			} else {
				// No regions defined yet - show helpful message
				ctx.fillStyle = "#ffffff80";
				ctx.font = "14px Arial";
				ctx.textAlign = "center";
				ctx.fillText("Add regions by adjusting x/y/width/height below", widgetX + backgroundWidth/2, widgetY + backgroundHeight/2);
			}

		},
	};

	node.addCustomWidget(widget);

	node.onResize = function (size) {
		computeCanvasSize(node, size);
	}

	// Force initial canvas size computation
	setTimeout(() => {
		computeCanvasSize(node, node.size);
	}, 100);

	return { minWidth: 200, minHeight: 280, widget }  // Fixed canvas height
}

app.registerExtension({
	name: "Comfy.EasyRegion.Simple",
	async beforeRegisterNodeDef(nodeType, nodeData, app) {
		if (nodeData.name === "EasyRegionSimple") {
			const onNodeCreated = nodeType.prototype.onNodeCreated;
			nodeType.prototype.onNodeCreated = function () {
				const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

				const defaultWidth = 512;
				const defaultHeight = 512;
				this.setProperty("width", defaultWidth)
				this.setProperty("height", defaultHeight)
				// Calculate percentage-based defaults (divisible by 8)
				this.setProperty("values", calculateDefaultRegions(defaultWidth, defaultHeight))

				this.selected = false

				this.serialize_widgets = true;

				// Add hidden widget to pass region boxes to Python
				this.addWidget("text", "region_boxes", JSON.stringify(this.properties["values"]), () => {}, {serialize: true});
				// Hide the widget (it's just for data passing)
				const boxWidget = this.widgets[this.widgets.length - 1];
				boxWidget.type = "converted-widget";
				boxWidget.hidden = true;

				// Add canvas after the prompt inputs
				addEasyRegionCanvas(this, app)

				// Dynamic region management based on prompts
				const node = this;
				const updateRegionsFromPrompts = () => {
					const defaultWidth = node.properties["width"] || (node.type === "EasyRegionMask" ? 1024 : 512);
					const defaultHeight = node.properties["height"] || (node.type === "EasyRegionMask" ? 1024 : 512);
					const currentValues = node.properties["values"] || [];

					// Check which region prompts have content
					const regionPrompts = [
						node.widgets.find(w => w.name === "region1_prompt"),
						node.widgets.find(w => w.name === "region2_prompt"),
						node.widgets.find(w => w.name === "region3_prompt"),
						node.widgets.find(w => w.name === "region4_prompt")
					];

					const newValues = [];
					for (let i = 0; i < regionPrompts.length; i++) {
						const prompt = regionPrompts[i]?.value || "";
						if (prompt.trim()) {
							// Region has content - ensure it has a box
							if (currentValues[i]) {
								// Keep existing box
								newValues.push(currentValues[i]);
							} else {
								// Create new box with percentage-based defaults
								const allRegions = calculateDefaultRegions(defaultWidth, defaultHeight);
								const defaultBox = allRegions[Math.min(i, allRegions.length - 1)];
								newValues.push(defaultBox);
							}
						} else {
							// Region is empty - don't include box
							newValues.push(null);
						}
					}

					// Remove null entries and update
					node.properties["values"] = newValues.filter(v => v !== null);

					// Update hidden widget
					const boxWidget = node.widgets.find(w => w.name === "region_boxes");
					if (boxWidget) {
						boxWidget.value = JSON.stringify(node.properties["values"]);
					}

					// Update region selector max
					const regionSelector = node.widgets[node.index];
					if (regionSelector) {
						regionSelector.options.max = Math.max(1, node.properties["values"].length);
						// Clamp current value
						if (regionSelector.value > node.properties["values"].length) {
							regionSelector.value = node.properties["values"].length;
						}
					}

					// Force canvas redraw
					if (app.graph) {
						app.graph.setDirtyCanvas(true, true);
					}
				};

				// Limit height of multiline prompt widgets to make node more compact
				const promptLabels = {
				"background_prompt": "🌍 Background Prompt:",
				"region1_prompt": "📍 Region 1:",
				"region2_prompt": "📍 Region 2:",
				"region3_prompt": "📍 Region 3:",
				"region4_prompt": "📍 Region 4:"
			};
			for (const w of this.widgets) {
				if (w.name in promptLabels) {
					// Set visible label header
					w.label = promptLabels[w.name];
					// Limit input height
					if (w.inputEl) {
						w.inputEl.style.maxHeight = "60px";  // ~3 lines of text
						w.inputEl.style.overflowY = "auto";
					}

					// Add callback to update regions when prompt changes
					if (w.name.startsWith("region")) {
						const originalCallback = w.callback;
						w.callback = function(value) {
							if (originalCallback) {
								originalCallback.call(this, value);
							}
							updateRegionsFromPrompts();
						};
					}
				}
			}

				// Find where index widget should be inserted (after canvas)
				const indexWidgetStartPos = this.widgets.length;
				this.index = indexWidgetStartPos;

				CUSTOM_INT(
					this,
					"region",
					1,  // Start at 1 (Region 1) not 0
					function (v, _, node) {
						let values = node.properties["values"]
						// v is now 1-based (1=Region 1, 2=Region 2, etc.)
						// Convert to 0-based array index
						const arrayIndex = v - 1;

						// Widget indices are after canvas and region selector
						const offset = indexWidgetStartPos + 1;
						if (arrayIndex >= 0 && arrayIndex < values.length && node.widgets.length > offset + 3) {
							// Update box dimension widgets (strength removed - now per-region inputs in Python)
							node.widgets[offset].value = values[arrayIndex][0]      // box_x
							node.widgets[offset + 1].value = values[arrayIndex][1]  // box_y
							node.widgets[offset + 2].value = values[arrayIndex][2]  // box_w
							node.widgets[offset + 3].value = values[arrayIndex][3]  // box_h
						}
					},
					{ step: 10, min: 1, max: 2, tooltip: "Select which region to edit (use box_x/y/w/h below to adjust position)" }
				)

				CUSTOM_INT(this, "box_x", 0, function (v, _, node) {transformFunc(this, v, node, 0)}, {tooltip: "X position of selected region (pixels from left)"})
				CUSTOM_INT(this, "box_y", 0, function (v, _, node) {transformFunc(this, v, node, 1)}, {tooltip: "Y position of selected region (pixels from top)"})
				CUSTOM_INT(this, "box_w", 0, function (v, _, node) {transformFunc(this, v, node, 2)}, {tooltip: "Width of selected region in pixels"})
				CUSTOM_INT(this, "box_h", 0, function (v, _, node) {transformFunc(this, v, node, 3)}, {tooltip: "Height of selected region in pixels"})
				// Strength slider removed - now using per-region strength inputs from Python

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
		if (node.type === "EasyRegionSimple") {
			node.widgets[node.index].options["max"] = node.properties["values"].length-1
		}
	},

});

app.registerExtension({
	name: "Comfy.EasyRegion.Mask",
	async beforeRegisterNodeDef(nodeType, nodeData, app) {
		if (nodeData.name === "EasyRegionMask") {
			const onNodeCreated = nodeType.prototype.onNodeCreated;
			nodeType.prototype.onNodeCreated = function () {
				const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

				const defaultWidth = 1344;
				const defaultHeight = 768;
				this.setProperty("width", defaultWidth)
				this.setProperty("height", defaultHeight)
				// Default regions matching user workflow (car, giraffe, bird)
				this.setProperty("values", [
					[0, 320, 368, 462, 2.0],      // Region 1 - red sports car (left)
					[448, 64, 384, 704, 2.0],     // Region 2 - giraffe (center-right)
					[945, 0, 378, 256, 2.0]       // Region 3 - blue bird (top-right)
				])

				this.selected = false

				this.serialize_widgets = true;

				// Add hidden widget to pass region boxes to Python
				this.addWidget("text", "region_boxes", JSON.stringify(this.properties["values"]), () => {}, {serialize: true});
				// Hide the widget (it's just for data passing)
				const boxWidget = this.widgets[this.widgets.length - 1];
				boxWidget.type = "converted-widget";
				boxWidget.hidden = true;

				// Add canvas after the prompt inputs
				addEasyRegionCanvas(this, app)

				// Dynamic region management based on prompts
				const node = this;
				const updateRegionsFromPrompts = () => {
					const defaultWidth = node.properties["width"] || (node.type === "EasyRegionMask" ? 1024 : 512);
					const defaultHeight = node.properties["height"] || (node.type === "EasyRegionMask" ? 1024 : 512);
					const currentValues = node.properties["values"] || [];

					// Check which region prompts have content
					const regionPrompts = [
						node.widgets.find(w => w.name === "region1_prompt"),
						node.widgets.find(w => w.name === "region2_prompt"),
						node.widgets.find(w => w.name === "region3_prompt"),
						node.widgets.find(w => w.name === "region4_prompt")
					];

					const newValues = [];
					for (let i = 0; i < regionPrompts.length; i++) {
						const prompt = regionPrompts[i]?.value || "";
						if (prompt.trim()) {
							// Region has content - ensure it has a box
							if (currentValues[i]) {
								// Keep existing box
								newValues.push(currentValues[i]);
							} else {
								// Create new box with percentage-based defaults
								const allRegions = calculateDefaultRegions(defaultWidth, defaultHeight);
								const defaultBox = allRegions[Math.min(i, allRegions.length - 1)];
								newValues.push(defaultBox);
							}
						} else {
							// Region is empty - don't include box
							newValues.push(null);
						}
					}

					// Remove null entries and update
					node.properties["values"] = newValues.filter(v => v !== null);

					// Update hidden widget
					const boxWidget = node.widgets.find(w => w.name === "region_boxes");
					if (boxWidget) {
						boxWidget.value = JSON.stringify(node.properties["values"]);
					}

					// Update region selector max
					const regionSelector = node.widgets[node.index];
					if (regionSelector) {
						regionSelector.options.max = Math.max(1, node.properties["values"].length);
						// Clamp current value
						if (regionSelector.value > node.properties["values"].length) {
							regionSelector.value = node.properties["values"].length;
						}
					}

					// Force canvas redraw
					if (app.graph) {
						app.graph.setDirtyCanvas(true, true);
					}
				};

				// Limit height of multiline prompt widgets to make node more compact
				const promptLabels = {
				"background_prompt": "🌍 Background Prompt:",
				"region1_prompt": "📍 Region 1:",
				"region2_prompt": "📍 Region 2:",
				"region3_prompt": "📍 Region 3:",
				"region4_prompt": "📍 Region 4:"
			};
			for (const w of this.widgets) {
				if (w.name in promptLabels) {
					// Set visible label header
					w.label = promptLabels[w.name];
					// Limit input height
					if (w.inputEl) {
						w.inputEl.style.maxHeight = "60px";  // ~3 lines of text
						w.inputEl.style.overflowY = "auto";
					}

					// Add callback to update regions when prompt changes
					if (w.name.startsWith("region")) {
						const originalCallback = w.callback;
						w.callback = function(value) {
							if (originalCallback) {
								originalCallback.call(this, value);
							}
							updateRegionsFromPrompts();
						};
					}
				}
			}

				// Find where index widget should be inserted (after canvas)
				const indexWidgetStartPos = this.widgets.length;
				this.index = indexWidgetStartPos;

				CUSTOM_INT(
					this,
					"region",
					1,  // Start at 1 (Region 1) not 0
					function (v, _, node) {
						let values = node.properties["values"]
						// v is now 1-based (1=Region 1, 2=Region 2, etc.)
						// Convert to 0-based array index
						const arrayIndex = v - 1;

						// Widget indices are after canvas and region selector
						const offset = indexWidgetStartPos + 1;
						if (arrayIndex >= 0 && arrayIndex < values.length && node.widgets.length > offset + 3) {
							// Update box dimension widgets (strength removed - now per-region inputs in Python)
							node.widgets[offset].value = values[arrayIndex][0]      // box_x
							node.widgets[offset + 1].value = values[arrayIndex][1]  // box_y
							node.widgets[offset + 2].value = values[arrayIndex][2]  // box_w
							node.widgets[offset + 3].value = values[arrayIndex][3]  // box_h
						}
					},
					{ step: 10, min: 1, max: 2, tooltip: "Select which region to edit (use box_x/y/w/h below to adjust position)" }
				)

				CUSTOM_INT(this, "box_x", 0, function (v, _, node) {transformFunc(this, v, node, 0)}, {tooltip: "X position of selected region (pixels from left)"})
				CUSTOM_INT(this, "box_y", 0, function (v, _, node) {transformFunc(this, v, node, 1)}, {tooltip: "Y position of selected region (pixels from top)"})
				CUSTOM_INT(this, "box_w", 0, function (v, _, node) {transformFunc(this, v, node, 2)}, {tooltip: "Width of selected region in pixels"})
				CUSTOM_INT(this, "box_h", 0, function (v, _, node) {transformFunc(this, v, node, 3)}, {tooltip: "Height of selected region in pixels"})
				// Strength slider removed - now using per-region strength inputs from Python

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
					const node = this;  // Capture node reference for closure
					widthWidget.callback = function(value) {
						const oldWidth = node.properties["width"] || 1024;
						const newWidth = value;
						const scale = newWidth / oldWidth;

						// Scale region X positions and widths proportionally
						if (node.properties["values"] && scale !== 1) {
							const scaledValues = node.properties["values"].map(region => {
								const [x, y, w, h, strength] = region;
								// Scale X position and width, keep Y and height unchanged
								return [
									Math.round(x * scale),
									y,
									Math.round(w * scale),
									h,
									strength
								];
							});
							node.properties["values"] = scaledValues;

							// Update hidden region_boxes widget
							const boxWidget = node.widgets.find(w => w.name === "region_boxes");
							if (boxWidget) {
								boxWidget.value = JSON.stringify(scaledValues);
							}

							// Update the box widgets to show new values
							const regionSelectorValue = node.widgets[node.index]?.value || 1;
							const arrayIndex = regionSelectorValue - 1;
							const offset = node.index + 1;
							if (arrayIndex >= 0 && arrayIndex < scaledValues.length && node.widgets.length > offset + 3) {
								node.widgets[offset].value = scaledValues[arrayIndex][0];      // box_x
								node.widgets[offset + 2].value = scaledValues[arrayIndex][2];  // box_w
							}
						}

						// Update canvas property to match
						node.properties["width"] = newWidth;
						// Force canvas redraw
						if (app.graph) {
							app.graph.setDirtyCanvas(true, true);
						}
						// Call original callback if it exists (with widget as context)
						if (originalWidthCallback) {
							originalWidthCallback.call(this, value);
						}
					};
				}

				if (heightWidget) {
					const originalHeightCallback = heightWidget.callback;
					const node = this;  // Capture node reference for closure
					heightWidget.callback = function(value) {
						const oldHeight = node.properties["height"] || 1024;
						const newHeight = value;
						const scale = newHeight / oldHeight;

						// Scale region Y positions and heights proportionally
						if (node.properties["values"] && scale !== 1) {
							const scaledValues = node.properties["values"].map(region => {
								const [x, y, w, h, strength] = region;
								// Scale Y position and height, keep X and width unchanged
								return [
									x,
									Math.round(y * scale),
									w,
									Math.round(h * scale),
									strength
								];
							});
							node.properties["values"] = scaledValues;

							// Update hidden region_boxes widget
							const boxWidget = node.widgets.find(w => w.name === "region_boxes");
							if (boxWidget) {
								boxWidget.value = JSON.stringify(scaledValues);
							}

							// Update the box widgets to show new values
							const regionSelectorValue = node.widgets[node.index]?.value || 1;
							const arrayIndex = regionSelectorValue - 1;
							const offset = node.index + 1;
							if (arrayIndex >= 0 && arrayIndex < scaledValues.length && node.widgets.length > offset + 3) {
								node.widgets[offset + 1].value = scaledValues[arrayIndex][1];  // box_y
								node.widgets[offset + 3].value = scaledValues[arrayIndex][3];  // box_h
							}
						}

						// Update canvas property to match
						node.properties["height"] = newHeight;
						// Force canvas redraw
						if (app.graph) {
							app.graph.setDirtyCanvas(true, true);
						}
						// Call original callback if it exists (with widget as context)
						if (originalHeightCallback) {
							originalHeightCallback.call(this, value);
						}
					};
				}

				return r;
			};
		}
	},
	loadedGraphNode(node, _) {
		if (node.type === "EasyRegionMask") {
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
