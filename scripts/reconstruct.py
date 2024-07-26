from datetime import datetime
import asyncio
from star_ray_xml import XMLState, XMLQuery, Update, Insert, Delete, Replace
from star_ray_pygame import View, WindowConfiguration

from icua.event import (
    MouseButtonEvent,
    MouseMotionEvent,
    KeyEvent,
    EyeMotionEvent,
    WindowCloseEvent,
    WindowOpenEvent,
    WindowFocusEvent,
    WindowMoveEvent,
    WindowResizeEvent,
)
from icua.event.event_guidance import (
    DrawBoxAction,
    DrawArrowAction,
    DrawBoxOnElementAction,
    DrawElementAction,
    ShowGuidance,
    ShowElementAction,
    HideElementAction,
)

from matbii.tasks import (
    SetPumpAction,
    BurnFuelAction,
    PumpFuelAction,
    TogglePumpFailureAction,
    TargetMoveAction,
    SetLightAction,
    ToggleLightAction,
    SetSliderAction,
)


CLASS_MAP = {
    cls.__name__: cls
    for cls in (
        Update,
        Insert,
        Delete,
        Replace,
        SetPumpAction,
        TogglePumpFailureAction,
        BurnFuelAction,
        PumpFuelAction,
        TargetMoveAction,
        SetLightAction,
        ToggleLightAction,
        SetSliderAction,
        MouseButtonEvent,
        MouseMotionEvent,
        KeyEvent,
        EyeMotionEvent,
        DrawBoxAction,
        DrawArrowAction,
        DrawBoxOnElementAction,
        DrawElementAction,
        ShowGuidance,
        ShowElementAction,
        HideElementAction,
        WindowCloseEvent,
        WindowOpenEvent,
        WindowFocusEvent,
        WindowMoveEvent,
        WindowResizeEvent,
    )
}


def parse_timestamp_to_ms(timestamp_str):
    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d-%H-%M-%S-%f")
    return timestamp.timestamp()


def parse_line(line, whitelist_classes=None):
    parts = line.split(" ", 2)
    if len(parts) != 3:
        raise ValueError(f"Malformed line: {line}")
    timestamp_str, class_name, data_str = parts
    timestamp = parse_timestamp_to_ms(timestamp_str)
    cls = CLASS_MAP.get(class_name, None)
    if cls is None:
        raise ValueError(f"Missing class: {class_name}")
    if whitelist_classes:
        if cls not in whitelist_classes:
            return None
    return timestamp, cls.model_validate_json(data_str)


def parse_events(file_path, whitelist=None):
    with open(file_path) as file:
        for line in file.readlines():
            result = parse_line(line, whitelist_classes=whitelist)
            if result:
                yield result


async def async_parse_events(file_path):
    gen = iter(list(parse_events(file_path)))

    t0, event = next(gen)
    for t, event in gen:
        await asyncio.sleep(t - t0)
        t0 = t
        yield event


async def main(file_path):
    # TODO load the config file that was used - is this logged anywhere?
    WIDTH, HEIGHT = 1000, 800
    NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}
    SVG = f"""<svg:svg width="{WIDTH}" height="{HEIGHT}" xmlns:svg="http://www.w3.org/2000/svg"></svg:svg>"""

    window_config = WindowConfiguration(
        width=WIDTH, height=HEIGHT, title="svg test", resizable=False, fullscreen=False
    )
    state = XMLState(xml=SVG, namespaces=NAMESPACES)
    view = View(window_config)

    async def _render_task():
        try:
            running = True
            while running:
                await asyncio.sleep(1 / 20)
                events = view.get_nowait()
                for event in events:
                    if isinstance(event, WindowCloseEvent):
                        running = False
                view.update(state.get_root()._base)
                view.render()
                if not running:
                    break
        except asyncio.CancelledError:
            pass
        finally:
            view.close()

    async def _event_task():
        try:
            async for event in async_parse_events(file_path):
                if isinstance(event, XMLQuery):
                    event.__execute__(state)
                else:
                    pass

        except asyncio.CancelledError:
            pass  # done

    render_task = asyncio.create_task(_render_task())
    event_task = asyncio.create_task(_event_task())

    _, pending = await asyncio.wait(
        (render_task, event_task), return_when=asyncio.FIRST_COMPLETED
    )
    for p in pending:
        p.cancel()

    # for timestamp, xml_event in tqdm(async_parse_events(file_path)):

    #     events = view.get_events()
    #     for event in events:
    #         if isinstance(event, WindowCloseEvent):
    #             running = False
    #     xml_event.__execute__(state)
    #     t1 = time.time()
    #     view.update(state.get_root()._base)
    #     view.render()
    #     ts.append(t1 - time.time())
    #     if not running:
    #         break


# Example usage:
if __name__ == "__main__":
    # Replace with your file path
    file_path = (
        "C:/Users/brjw/Documents/repos/logs/event_log_xml_2024-07-11-16-33-19.log"
        # "C:/Users/brjw/Documents/repos/logs/event_log_2024-07-11-16-33-19.log"
    )

    parse_events(file_path)
    asyncio.run(main(file_path))
