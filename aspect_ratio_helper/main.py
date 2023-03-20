import contextlib
from functools import partial

import gradio as gr
from modules import script_callbacks
from modules import scripts
from modules import shared
from modules.shared import opts

from aspect_ratio_helper._util import _DEFAULT_DISPLAY_KEY
from aspect_ratio_helper._util import _MAX_DIMENSION
from aspect_ratio_helper._util import _MIN_DIMENSION
from aspect_ratio_helper._util import _PREDEFINED_PERCENTAGES_DISPLAY_MAP
from aspect_ratio_helper._util import _scale_by_percentage
from aspect_ratio_helper._util import _scale_dimensions_to_max_dimension


_EXTENSION_NAME = 'Aspect Ratio Helper'


def on_ui_settings():
    section = 'aspect_ratio_helper', _EXTENSION_NAME
    shared.opts.add_option(
        key='arh_expand_by_default',
        info=shared.OptionInfo(
            default=False,
            label='Expand by default',
            section=section,
        ),
    )
    shared.opts.add_option(
        key='arh_show_max_width_or_height',
        info=shared.OptionInfo(
            default=True,
            label='Show maximum width or height button',
            section=section,
        ),
    )
    shared.opts.add_option(
        key='arh_max_width_or_height',
        info=shared.OptionInfo(
            default=_MAX_DIMENSION / 2,
            label='Maximum width or height default',
            component=gr.Slider,
            component_args={
                'minimum': _MIN_DIMENSION,
                'maximum': _MAX_DIMENSION,
                'step': 1,
            },
            section=section,
        ),
    )
    shared.opts.add_option(
        key='arh_show_predefined_percentages',
        info=shared.OptionInfo(
            default=True,
            label='Show predefined percentage buttons',
            section=section,
        ),
    )
    shared.opts.add_option(
        key='arh_predefined_percentages',
        info=shared.OptionInfo(
            default='25, 50, 75, 125, 150, 175, 200',
            label='Predefined percentage buttons, applied to dimensions (75, '
                  '125, 150)',
            section=section,
        ),
    )
    shared.opts.add_option(
        key='arh_predefined_percentages_display_key',
        info=shared.OptionInfo(
            default=_DEFAULT_DISPLAY_KEY,
            label='Predefined percentage display format',
            component=gr.Dropdown,
            component_args=lambda: {
                'choices': tuple(_PREDEFINED_PERCENTAGES_DISPLAY_MAP.keys()),
            },
            section=section,
        ),
    )


class AspectRatioStepScript(scripts.Script):

    def title(self):
        return _EXTENSION_NAME

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        if not any([
            opts.arh_show_max_width_or_height,
            opts.arh_show_predefined_percentages,
        ]):
            return  # return early as no 'show' options enabled

        with (
            gr.Group(),
            gr.Accordion(_EXTENSION_NAME, open=opts.arh_expand_by_default),
            contextlib.suppress(AttributeError),
        ):
            if is_img2img:
                inputs = outputs = [self.i2i_w, self.i2i_h]
            else:
                inputs = outputs = [self.t2i_w, self.t2i_h]

            if opts.arh_show_max_width_or_height:
                with gr.Row():
                    max_dimension = gr.inputs.Slider(
                        minimum=_MIN_DIMENSION,
                        maximum=_MAX_DIMENSION,
                        step=1,
                        default=opts.arh_max_width_or_height,
                        label='Maximum width or height (whichever is higher)',
                    )
                    gr.Button(value='Scale to maximum width or height').click(
                        fn=_scale_dimensions_to_max_dimension,
                        inputs=[*inputs, max_dimension],
                        outputs=outputs,
                    )

            if opts.arh_show_predefined_percentages:
                display_func = _PREDEFINED_PERCENTAGES_DISPLAY_MAP.get(
                    opts.arh_predefined_percentages_display_key,
                )
                with gr.Column(variant='panel'), gr.Row(variant='compact'):
                    pps = opts.arh_predefined_percentages
                    percentages = [
                        abs(int(x)) for x in pps.split(',')
                    ]
                    for percentage in percentages:
                        gr.Button(value=display_func(percentage)).click(
                            fn=partial(
                                _scale_by_percentage, pct=percentage / 100,
                            ),
                            inputs=inputs,
                            outputs=outputs,
                        )

    def after_component(self, component, **kwargs):
        element_id = kwargs.get('elem_id')

        if element_id == 'txt2img_width':
            self.t2i_w = component
        elif element_id == 'txt2img_height':
            self.t2i_h = component
        elif element_id == 'img2img_width':
            self.i2i_w = component
        elif element_id == 'img2img_height':
            self.i2i_h = component


script_callbacks.on_ui_settings(on_ui_settings)
