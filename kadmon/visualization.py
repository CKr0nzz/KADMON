"""Figures comparatives et animation FURY des déplacements KADMON."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class _AnimatedGeometry:
    """Géométrie nécessaire pour interpoler un acteur FURY."""

    polydata: Any
    source: np.ndarray
    projection: np.ndarray


@dataclass
class _AnimationState:
    """État mutable partagé par les callbacks de l'interface."""

    frame_count: int
    frame: int = 0
    playing: bool = False
    updating_slider: bool = False


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
    from vtkmodules.vtkRenderingCore import (
        vtkActor2D,
        vtkPolyDataMapper2D,
        vtkTextActor,
    )

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


def _validate_animation_parameters(
    *,
    cycle_duration_s: float,
    frames_per_second: int,
    minimum_visible_displacement_mm: float,
    color_upper_percentile: float,
) -> None:
    """Valider les paramètres numériques de l'animation."""
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


def _prepare_animation_data(
    results: dict[str, object] | dict[str, dict[str, object]],
) -> list[dict[str, np.ndarray]]:
    """Normaliser une fois les résultats et vérifier les déplacements finis."""
    named_results = {"bundle": results} if "barycentric" in results else results
    if not named_results:
        raise ValueError("Au moins un résultat est requis.")

    prepared = [_visualization_data(result) for result in named_results.values()]
    finite_displacements = [
        values[np.isfinite(values)]
        for data in prepared
        if (values := data["point_mm"][data["valid"]]).size
    ]
    if not finite_displacements or not any(
        values.size for values in finite_displacements
    ):
        raise ValueError("Aucun déplacement fini à afficher.")
    return prepared


def _amplitude_scale(
    prepared: list[dict[str, np.ndarray]],
    *,
    colormap: str,
    upper_percentile: float,
):
    """Construire l'échelle colorimétrique commune aux résultats."""
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize

    finite_displacements = np.concatenate(
        [
            values[np.isfinite(values)]
            for data in prepared
            if (values := data["point_mm"][data["valid"]]).size
        ]
    )
    upper_mm = float(np.percentile(finite_displacements, upper_percentile))
    limits = (0.0, max(upper_mm, np.finfo(float).eps))
    return limits, Normalize(*limits, clip=True), plt.get_cmap(colormap)


def _add_displacement_actors(
    scene,
    prepared: list[dict[str, np.ndarray]],
    *,
    amplitude_norm,
    amplitude_cmap,
    minimum_visible_displacement_mm: float,
) -> list[_AnimatedGeometry]:
    """Créer les acteurs et conserver leur géométrie interpolable."""
    from fury import actor

    animated = []
    for data in prepared:
        source = data["source_reps"][data["valid"]]
        projection = data["projection"][data["valid"]]
        if not len(source):
            continue
        vectors = projection - source
        point_mm = np.linalg.norm(vectors, axis=-1).reshape(-1)
        colors = amplitude_cmap(amplitude_norm(point_mm))[:, :3]
        colors[point_mm <= minimum_visible_displacement_mm] = 0.0
        moving_actor = actor.line(
            source, colors=colors, opacity=1.0, linewidth=3.0, lod=False
        )
        scene.add(moving_actor)
        animated.append(
            _AnimatedGeometry(moving_actor.GetMapper().GetInput(), source, projection)
        )
    if not animated:
        raise ValueError("Aucun représentant source n'a reçu de masse.")
    return animated


def _create_animation_controls(ui, size: tuple[int, int]):
    """Créer le slider temporel et le bouton lecture/pause."""
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
    return timeline, play_button


def _configure_animation_callbacks(
    *,
    animated: list[_AnimatedGeometry],
    state: _AnimationState,
    timeline,
    play_button,
    manager,
    timer_interval_ms: int,
) -> None:
    """Relier géométrie, contrôles et timer à l'état de lecture."""
    from vtkmodules.util.numpy_support import numpy_to_vtk

    def apply_phase(phase: float) -> None:
        for geometry in animated:
            positions = np.ascontiguousarray(
                (
                    (1.0 - phase) * geometry.source
                    + phase * geometry.projection
                ).reshape(-1, 3),
                dtype=np.float64,
            )
            points = geometry.polydata.GetPoints()
            points.SetData(numpy_to_vtk(positions, deep=True))
            points.Modified()
            geometry.polydata.Modified()

    def scrub_animation(slider) -> None:
        if state.updating_slider:
            return
        phase = float(slider.ratio)
        apply_phase(phase)
        ascending_angle = np.arccos(np.clip(1.0 - 2.0 * phase, -1.0, 1.0))
        state.frame = round(ascending_angle * state.frame_count / (2.0 * np.pi))
        state.playing = False
        play_button.message = "PLAY"
        manager.render()

    def toggle_animation(i_ren, _obj, _button) -> None:
        state.playing = not state.playing
        play_button.message = "PAUSE" if state.playing else "PLAY"
        i_ren.event.abort()
        manager.render()

    def update_animation(_obj, _event) -> None:
        if not state.playing:
            return
        phase = 0.5 - 0.5 * np.cos(2.0 * np.pi * state.frame / state.frame_count)
        apply_phase(phase)
        state.updating_slider = True
        try:
            timeline.value = 100.0 * phase
        finally:
            state.updating_slider = False
        state.frame = (state.frame + 1) % state.frame_count
        manager.render()

    timeline.on_change = scrub_animation
    play_button.on_left_mouse_button_clicked = toggle_animation
    manager.add_timer_callback(True, timer_interval_ms, update_animation)


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
    obtenue par interpolation linéaire entre chaque représentant source et sa
    projection barycentrique. Elle représente le vecteur barycentrique OT, et
    non une trajectoire anatomique ou une déformation physique.
    """
    from fury import ui, window

    _validate_animation_parameters(
        cycle_duration_s=cycle_duration_s,
        frames_per_second=frames_per_second,
        minimum_visible_displacement_mm=minimum_visible_displacement_mm,
        color_upper_percentile=color_upper_percentile,
    )
    prepared = _prepare_animation_data(results)
    limits, amplitude_norm, amplitude_cmap = _amplitude_scale(
        prepared,
        colormap=amplitude_colormap,
        upper_percentile=color_upper_percentile,
    )

    scene = window.Scene()
    scene.background((0.04, 0.04, 0.06))
    animated = _add_displacement_actors(
        scene,
        prepared,
        amplitude_norm=amplitude_norm,
        amplitude_cmap=amplitude_cmap,
        minimum_visible_displacement_mm=minimum_visible_displacement_mm,
    )

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
    timeline, play_button = _create_animation_controls(ui, size)
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
    state = _AnimationState(
        frame_count=max(2, round(cycle_duration_s * frames_per_second))
    )
    _configure_animation_callbacks(
        animated=animated,
        state=state,
        timeline=timeline,
        play_button=play_button,
        manager=manager,
        timer_interval_ms=max(1, round(1000 / frames_per_second)),
    )
    manager.render()
    print("Animation OT : 0 % = source; 100 % = projection barycentrique.")
    print(
        f"La couleur code l'amplitude 0–{limits[1]:.2f} mm "
        f"({upper_caption}); la direction est portée par l'animation."
    )
    print(
        "Le bouton PLAY/PAUSE contrôle l'animation; "
        "déplacer le slider la met en pause."
    )
    if interactive:
        manager.start()
    return scene, manager
