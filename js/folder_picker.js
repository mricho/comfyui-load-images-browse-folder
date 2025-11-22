import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
	name: "Antigravity.FolderBrowser",
	async beforeRegisterNodeDef(nodeType, nodeData, app) {
		if (nodeData.name === "LoadImagesFromFolder") {
			const onNodeCreated = nodeType.prototype.onNodeCreated;
			nodeType.prototype.onNodeCreated = function () {
				const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

				const folderWidget = this.widgets.find((w) => w.name === "folder_path");
				if (folderWidget) {
					const btn = this.addWidget("button", "Browse", "Browse", () => {
						const currentPath = folderWidget.value;
						showFolderPicker(currentPath, (selectedPath) => {
							folderWidget.value = selectedPath;
						});
					});
				}

				return r;
			};
		}
	},
});

function showFolderPicker(initialPath, onSelect) {
	const dialog = document.createElement("div");
	Object.assign(dialog.style, {
		position: "fixed",
		top: "50%",
		left: "50%",
		transform: "translate(-50%, -50%)",
		width: "600px",
		height: "500px",
		backgroundColor: "#222",
		border: "1px solid #444",
		borderRadius: "8px",
		zIndex: "10000",
		display: "flex",
		flexDirection: "column",
		padding: "10px",
		color: "#fff",
		fontFamily: "sans-serif",
		boxShadow: "0 4px 12px rgba(0,0,0,0.5)"
	});

	const header = document.createElement("div");
	Object.assign(header.style, {
		display: "flex",
		justifyContent: "space-between",
		alignItems: "center",
		marginBottom: "10px",
		borderBottom: "1px solid #444",
		paddingBottom: "5px"
	});

	const title = document.createElement("h3");
	title.textContent = "Select Folder";
	title.style.margin = "0";

	const closeBtn = document.createElement("button");
	closeBtn.textContent = "✕";
	Object.assign(closeBtn.style, {
		background: "transparent",
		border: "none",
		color: "#aaa",
		cursor: "pointer",
		fontSize: "18px"
	});
	closeBtn.onclick = () => document.body.removeChild(dialog);

	header.appendChild(title);
	header.appendChild(closeBtn);
	dialog.appendChild(header);

	const pathDisplay = document.createElement("div");
	pathDisplay.style.marginBottom = "10px";
	pathDisplay.style.fontSize = "14px";
	pathDisplay.style.color = "#aaa";
	pathDisplay.textContent = initialPath || "Loading...";
	dialog.appendChild(pathDisplay);

	const listContainer = document.createElement("div");
	Object.assign(listContainer.style, {
		flex: "1",
		overflowY: "auto",
		border: "1px solid #333",
		backgroundColor: "#111",
		borderRadius: "4px",
		padding: "5px"
	});
	dialog.appendChild(listContainer);

	const footer = document.createElement("div");
	Object.assign(footer.style, {
		display: "flex",
		justifyContent: "flex-end",
		marginTop: "10px",
		gap: "10px"
	});

	const selectBtn = document.createElement("button");
	selectBtn.textContent = "Select Current Folder";
	Object.assign(selectBtn.style, {
		padding: "8px 16px",
		backgroundColor: "#2a6",
		border: "none",
		borderRadius: "4px",
		color: "#fff",
		cursor: "pointer"
	});
	
	let currentPath = initialPath;

	selectBtn.onclick = () => {
		if (currentPath) {
			onSelect(currentPath);
			document.body.removeChild(dialog);
		}
	};

	footer.appendChild(selectBtn);
	dialog.appendChild(footer);

	document.body.appendChild(dialog);

	async function loadPath(path) {
		try {
			const response = await api.fetchApi("/antigravity/browse/get_directory", {
				method: "POST",
				body: JSON.stringify({ path: path }),
			});
			
			if (!response.ok) {
				const err = await response.json();
				alert("Error: " + (err.error || response.statusText));
				return;
			}

			const data = await response.json();
			currentPath = data.current_path;
			pathDisplay.textContent = currentPath;
			listContainer.innerHTML = "";

			// Parent directory link
			if (data.parent_path && data.parent_path !== data.current_path) {
				const parentDiv = document.createElement("div");
				parentDiv.textContent = "📁 ..";
				Object.assign(parentDiv.style, {
					padding: "5px",
					cursor: "pointer",
					userSelect: "none"
				});
				parentDiv.onmouseover = () => parentDiv.style.backgroundColor = "#333";
				parentDiv.onmouseout = () => parentDiv.style.backgroundColor = "transparent";
				parentDiv.onclick = () => loadPath(data.parent_path);
				listContainer.appendChild(parentDiv);
			}

			data.items.forEach(item => {
				const itemDiv = document.createElement("div");
				itemDiv.textContent = "📁 " + item.name;
				Object.assign(itemDiv.style, {
					padding: "5px",
					cursor: "pointer",
					userSelect: "none",
					whiteSpace: "nowrap",
					overflow: "hidden",
					textOverflow: "ellipsis"
				});
				itemDiv.onmouseover = () => itemDiv.style.backgroundColor = "#333";
				itemDiv.onmouseout = () => itemDiv.style.backgroundColor = "transparent";
				itemDiv.onclick = () => loadPath(item.path);
				listContainer.appendChild(itemDiv);
			});

		} catch (e) {
			console.error(e);
			alert("Failed to load directory: " + e.message);
		}
	}

	loadPath(initialPath);
}
