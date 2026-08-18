"""Figures comparatives et animation FURY des déplacements KADMON."""

from __future__ import annotations

import numpy as np


def _visualization_data(result: dict[str, object]) -> dict[str, np.ndarray]:
    """Extraire et valider les tableaux nécessaires aux figures."""
    barycentric = result["barycentric"]
    source_reps = np.asarray(result["source_representatives"], dtype=np.float64)
    valid = np.asarray(barycentric["valid_mask"], dtype=bool)
    point_mm = np.asarray(barycentric["point_displacement_mm"], dtype=np.float64)
    row_mass = np.asarray(barycentric["row_mass"], dtype=np.float64)
    source_weights = np.asarray(result["source_weights"], dtype=np.float64)
    if source_reps.ndim != 3 or source_reps.shape[-1] != 3:
        raise ValueError("Les représentants source doivent avoir la forme (N, P, 3).")
    if (
        valid.shape != (len(source_reps),)
        or row_mass.shape != (len(source_reps),)
        or source_weights.shape != (len(source_reps),)
        or point_mm.shape != source_reps.shape[:2]
    ):
        raise ValueError("Les données barycentriques sont incompatibles.")
    return {
        "source": np.asarray(result["source_streamlines"], dtype=np.float64),
        "target": np.asarray(result["target_streamlines"], dtype=np.float64),
        "source_reps": source_reps,
        "target_reps": np.asarray(result["target_representatives"], dtype=np.float64),
        "projection": np.asarray(barycentric["projection"], dtype=np.float64),
        "vectors": np.asarray(barycentric["displacement_vectors"], dtype=np.float64),
        "point_mm": point_mm,
        "row_mass": row_mass,
        "source_weights": source_weights,
        "transport_support": np.divide(
            row_mass,
            source_weights,
            out=np.zeros_like(row_mass),
            where=source_weights > 0,
        ).clip(0, 1),
        "valid": valid,
    }


def _add_amplitude_legend(
    scene,
    limits_mm: tuple[float, float],
    upper_caption: str,
    *,
    amplitude_colors: np.ndarray,
    viewport_center: int = 400,
) -> None:
    """Ajouter l'échelle 2D des déplacements en millimètres."""
    from vtkmodules.vtkCommonCore import vtkPoints
    from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData
    from vtkmodules.vtkRenderingCore import vtkActor2D, vtkPolyDataMapper2D, vtkTextActor

    def add_text(
        text: str,
        position: tuple[int, int],
        *,
        color: tuple[float, float, float] = (0.92, 0.92, 0.92),
        size: int = 15,
        bold: bool = False,
        centered: bool = False,
    ) -> None:
        label = vtkTextActor()
        label.SetInput(text)
        label.SetPosition(*position)
        prop = label.GetTextProperty()
        prop.SetFontSize(size)
        prop.SetColor(*color)
        prop.SetBold(bold)
        prop.SetShadow(True)
        if centered:
            prop.SetJustificationToCentered()
        scene.add(label)

    def add_swatch(
        position: tuple[int, int],
        color: tuple[float, float, float],
        *,
        size: int = 18,
    ) -> None:
        x0, y0 = position
        points = vtkPoints()
        for point in (
            (x0, y0, 0), (x0 + size, y0, 0),
            (x0 + size, y0 + size, 0), (x0, y0 + size, 0),
        ):
            points.InsertNextPoint(*point)
        polygon = vtkCellArray()
        polygon.InsertNextCell(4)
        for index in range(4):
            polygon.InsertCellPoint(index)
        data = vtkPolyData()
        data.SetPoints(points)
        data.SetPolys(polygon)
        mapper = vtkPolyDataMapper2D()
        mapper.SetInputData(data)
        swatch = vtkActor2D()
        swatch.SetMapper(mapper)
        swatch.GetProperty().SetColor(*color)
        scene.add(swatch)

    swatch_size = 24
    ramp_x = viewport_center - len(amplitude_colors) * swatch_size // 2
    for index, color in enumerate(amplitude_colors):
        add_swatch((ramp_x + index * swatch_size, 72), tuple(color), size=swatch_size)
    add_text("0", (ramp_x - 28, 76), size=14, centered=True)
    add_text(
        f"{limits_mm[1]:.2f} mm",
        (ramp_x + len(amplitude_colors) * swatch_size + 38, 76),
        size=14, centered=True,
    )
    add_text(
        f">= {upper_caption} clippe", (viewport_center, 35),
        size=13, centered=True,
    )


def animate_local_displacements_3d(
    results: dict[str, object] | dict[str, dict[str, object]],
    *,
    cycle_duration_s: float = 4.0,
    frames_per_second: int = 30,
    minimum_visible_displacement_mm: float = 0.0,
    amplitude_colormap: str = "magma",
    color_upper_percentile: float = 95.0,
    interactive: bool = True,
    size: tuple[int, int] = (1400, 1000),
):
    """Animer l'interpolation source-projection des déplacements OT.

    Une période complète effectue un aller-retour. La trajectoire droite est
    une représentation du vecteur barycentrique OT, et non une trajectoire
    anatomique ou une déformation physique.
    """
    from fury import actor, ui, window
    from vtkmodules.util.numpy_support import numpy_to_vtk

    if cycle_duration_s <= 0:
        raise ValueError("cycle_duration_s doit être strictement positif.")
    if frames_per_second < 1:
        raise ValueError("frames_per_second doit être strictement positif.")
    if minimum_visible_displacement_mm < 0:
        raise ValueError(
            "minimum_visible_displacement_mm doit être positif ou nul."
        )
    if not 0 < color_upper_percentile <= 100:
        raise ValueError("color_upper_percentile doit appartenir à ]0, 100].")

    if "barycentric" in results:
        named_results = {"bundle": results}
    else:
        named_results = results
    if not named_results:
        raise ValueError("Au moins un résultat est requis.")

    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize

    displacement_values = []
    for result in named_results.values():
        data = _visualization_data(result)
        values = data["point_mm"][data["valid"]]
        displacement_values.append(values[np.isfinite(values)])
    finite_displacements = np.concatenate(displacement_values)
    if not finite_displacements.size:
        raise ValueError("Aucun déplacement fini à afficher.")
    upper_mm = float(np.percentile(finite_displacements, color_upper_percentile))
    limits = (0.0, max(upper_mm, np.finfo(float).eps))
    amplitude_norm = Normalize(*limits, clip=True)
    amplitude_cmap = plt.get_cmap(amplitude_colormap)

    scene = window.Scene()
    scene.background((0.04, 0.04, 0.06))
    animated = []
    for name, result in named_results.items():
        data = _visualization_data(result)
        source = data["source_reps"][data["valid"]]
        projection = data["projection"][data["valid"]]
        if not len(source):
            continue
        vectors = projection - source
        point_mm = np.linalg.norm(vectors, axis=-1)
        colors = amplitude_cmap(amplitude_norm(point_mm.reshape(-1)))[:, :3]
        colors[point_mm.reshape(-1) <= minimum_visible_displacement_mm] = 0.0
        moving_actor = actor.line(
            source,
            colors=colors,
            opacity=1.0,
            linewidth=3.0,
            lod=False,
        )
        scene.add(moving_actor)
        animated.append((moving_actor.GetMapper().GetInput(), source, vectors))

    if not animated:
        raise ValueError("Aucun représentant source n'a reçu de masse.")

    legend_levels = np.linspace(limits[0], limits[1], 12)
    legend_colors = amplitude_cmap(amplitude_norm(legend_levels))[:, :3]
    upper_caption = (
        "maximum" if color_upper_percentile == 100
        else f"P{color_upper_percentile:g}"
    )
    _add_amplitude_legend(
        scene,
        limits,
        upper_caption,
        amplitude_colors=legend_colors,
        viewport_center=size[0] // 2,
    )
    timeline = ui.LineSlider2D(
        center=(size[0] / 2, 145),
        initial_value=0,
        min_value=0,
        max_value=100,
        length=min(650, size[0] * 0.55),
        line_width=6,
        outer_radius=11,
        font_size=16,
        text_template="Source vers projection : {ratio:.0%}",
    )
    timeline.track.color = (0.35, 0.35, 0.38)
    timeline.default_color = (1.0, 0.72, 0.30)
    timeline.active_color = timeline.default_color
    timeline.handle.color = timeline.default_color
    play_button = ui.TextBlock2D(
        text="PLAY", font_size=16, bold=True,
        justification="center", vertical_justification="middle",
        size=(90, 36), color=(1.0, 1.0, 1.0),
    )
    scene.reset_camera()
    manager = window.ShowManager(
        scene=scene,
        title="KADMON — Animation des déplacements OT",
        size=size,
        reset_camera=False,
    )
    manager.initialize()
    actual_width, actual_height = manager.window.GetSize()
    timeline.center = (
        actual_width / 2 + 55,
        max(90, min(145, actual_height * 0.16)),
    )
    play_button.position = (
        timeline.left_x_position - 115,
        timeline.center[1] - 18,
    )
    scene.add(timeline)
    scene.add(play_button)
    frame_count = max(2, round(cycle_duration_s * frames_per_second))
    state = {"frame": 0, "playing": False, "updating_slider": False}

    def apply_phase(phase: float) -> None:
        for polydata, source, vectors in animated:
            positions = np.ascontiguousarray(
                (source + phase * vectors).reshape(-1, 3), dtype=np.float64,
            )
            polydata.GetPoints().SetData(numpy_to_vtk(positions, deep=True))
            polydata.GetPoints().Modified()
            polydata.Modified()

    def scrub_animation(slider) -> None:
        if state["updating_slider"]:
            return
        phase = float(slider.ratio)
        apply_phase(phase)
        ascending_angle = np.arccos(np.clip(1.0 - 2.0 * phase, -1.0, 1.0))
        state["frame"] = round(ascending_angle * frame_count / (2.0 * np.pi))
        state["playing"] = False
        play_button.message = "PLAY"
        manager.render()

    timeline.on_change = scrub_animation

    def toggle_animation(i_ren, _obj, _button) -> None:
        state["playing"] = not state["playing"]
        play_button.message = "PAUSE" if state["playing"] else "PLAY"
        i_ren.event.abort()
        manager.render()

    play_button.on_left_mouse_button_clicked = toggle_animation

    def update_animation(_obj, _event) -> None:
        if not state["playing"]:
            return
        phase = 0.5 - 0.5 * np.cos(
            2.0 * np.pi * state["frame"] / frame_count
        )
        apply_phase(phase)
        state["updating_slider"] = True
        try:
            timeline.value = 100.0 * phase
        finally:
            state["updating_slider"] = False
        state["frame"] = (state["frame"] + 1) % frame_count
        manager.render()

    manager.add_timer_callback(
        True,
        max(1, round(1000 / frames_per_second)),
        update_animation,
    )
    manager.render()
    print("Animation OT : 0 % = source; 100 % = projection barycentrique.")
    print(
        f"La couleur code l'amplitude 0–{limits[1]:.2f} mm "
        f"({upper_caption}); la direction est portée par l'animation."
    )
    print("Le bouton PLAY/PAUSE contrôle l'animation; déplacer le slider la met en pause.")
    if interactive:
        manager.start()
    return scene, manager
