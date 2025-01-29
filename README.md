# Blender LOD Generator Add-On 🔧  
**Work in Progress** | *Goal: Simplify optimized model creation for real-time applications*

---

## 📖 Description  
The **LOD Generator** is an evolving Blender add-on designed to automate Level-of-Detail (LOD) creation and texture optimization. While still in development, its goal is to become a powerful tool for artists and developers working with real-time applications (games, VR/AR, etc.), reducing manual work and ensuring performance-friendly assets.

---

## 🚀 Current Features  
- **Auto-LOD Generation**  
  - Create multiple LOD versions with customizable face reduction percentages.  
  - Sequential decimation (each LOD builds on the previous).  
- **Smart Texture Resizing**  
  - Resizes textures proportionally (supports `.png`, `.jpg`/`.jpeg`).  
  - Minimum resolution enforced at **512px** to avoid artifacts.  
  - Handles UV-tiled textures (e.g., `<UVTILE>` naming).  
- **Organized Workflow**  
  - Dedicated UI in the 3D View sidebar (`N` > **LOD Tools**).  
  - Generates `LOD1`, `LOD2` folders for textures/models.  
  - Options to **replace** or **skip** existing textures.  

---

## 🔜 Planned Improvements  
- Support for additional texture formats (e.g., `.tga`, `.exr`).  
- Advanced decimation methods (planar, symmetry-based).  
- Batch processing for multiple objects.  
- Preset systems for common LOD workflows.  

---

## 🛠️ Installation  
1. Download the latest `.py` file from the [Releases](https://github.com/yourusername/yourrepo/releases) section.  
2. In Blender: `Edit > Preferences > Add-ons > Install...`.  
3. Enable the add-on under the **Object** category.  

---

## 🖱️ Basic Usage  
1. **Prepare:**  
   - Save your `.blend` file.  
   - Ensure textures are **externally saved** (not packed).  
2. **Configure:**  
   - Select your model.  
   - Open the **LOD Tools** sidebar (`N` key).  
   - Set LOD count and reduction percentage.  
3. **Generate:**  
   - Click *Generate LODs*.  
   - Monitor progress in Blender's info header.  

---

## ⚠️ Important Notes  
- This is a **work in progress**—back up your files before use!  
- Textures must be saved externally (not packed in `.blend`).  
- Provide feedback via [GitHub Issues]

---

## 📃 License  
MIT License - Free for personal and commercial use.  
