from tethys_sdk.base import TethysAppBase, url_map_maker



class FloodRisk(TethysAppBase):
    """
    Tethys app class for Flood Risk.
    """

    name = 'Flood Risk'
    index = 'flood_risk:home'
    icon = 'flood_risk/images/icon.gif'
    package = 'flood_risk'
    root_url = 'flood-risk'
    color = '#056eb7'
    description = 'Application used to determine flood risk. Developed by AE2S.'
    tags = '"#056eb7"'
    enable_feedback = False
    feedback_emails = []

    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (
            UrlMap(
                name='home',
                url='flood-risk',
                controller='flood_risk.controllers.home'
            ),
            UrlMap(
                name='layer_gen',
                url='layer-gen/layers',
                controller='flood_risk.controllers.layer_gen'
            ),
            UrlMap(
                name='risk_analysis',
                url='risk-analysis/risks',
                controller='flood_risk.controllers.risk_analysis'
            ),
            UrlMap(
                name='building_process_ajax',
                url='flood-risk/layer-gen/layers/building-process-ajax',
                controller='flood_risk.ajax_controllers.building_process'
            ),

            UrlMap(
                name='raster_process_ajax',
                url='layer-gen/layers/raster-process-ajax',
                controller='flood_risk.ajax_controllers.raster_process'
            ),
            UrlMap(
                name='tax_process_ajax',
                url='layer-gen/layers/tax-process-ajax',
                controller='flood_risk.ajax_controllers.tax_process'
            ),
            UrlMap(
                name='tax_process2_ajax',
                url='layer-gen/layers/tax-process2-ajax',
                controller='flood_risk.ajax_controllers.tax_process2'
            ),
            UrlMap(
                name='land_process_ajax',
                url='layer-gen/layers/land-process-ajax',
                controller='flood_risk.ajax_controllers.land_process'
            ),
            UrlMap(
                name='land_process2_ajax',
                url='layer-gen/layers/land-process2-ajax',
                controller='flood_risk.ajax_controllers.land_process2'
            ),
            UrlMap(
                name='streets_process_ajax',
                url='flood-risk/risk-analysis/risks/streets-process-ajax',
                controller='flood_risk.ajax_controllers.streets_process'
            ),
            UrlMap(
                name='streets_process2_ajax',
                url='flood-risk/risk-analysis/risks/streets-process2-ajax',
                controller='flood_risk.ajax_controllers.streets_process2'
            )
        )

        return url_maps
