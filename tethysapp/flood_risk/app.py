from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.app_settings import SpatialDatasetServiceSetting



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
                name='manhole',
                url='manhole',
                controller='flood_risk.controllers.manhole'
            ),
            UrlMap(
                name='building_process_ajax',
                url='flood-risk/layer-gen/layers/building-process-ajax',
                controller='flood_risk.ajax_controllers.building_process'
            ),
            UrlMap(
                name='streets_process_ajax',
                url='flood-risk/risk-analysis/risks/streets-process-ajax',
                controller='flood_risk.ajax_controllers.streets_process'
            ),
            UrlMap(
                name='manhole_process_ajax',
                url='flood-risk/manhole/manhole-process-ajax',
                controller='flood_risk.ajax_controllers.manhole_process'
            ),
            UrlMap(
                name='file-upload',
                url='flood-risk/layer-gen/layers/file-upload',
                controller='flood_risk.ajax_controllers.file_upload'
            ),
            UrlMap(
                name='file-upload-move-files',
                url='flood-risk/layer-gen/layers/file-upload-move-files',
                controller='flood_risk.ajax_controllers.file_upload_move_files'
            ),
            UrlMap(
                name='file-upload',
                url='flood-risk/risk-analysis/risks/file-upload',
                controller='flood_risk.ajax_controllers.file_upload'
            ),
            UrlMap(
                name='file-upload',
                url='flood-risk/manhole/file-upload',
                controller='flood_risk.ajax_controllers.file_upload'
            ),
        )

        return url_maps

    def spatial_dataset_service_settings(self):
        """
        spatial_dataset_service_settings method for FloodRisk App
        """
        sds_settings = (
            SpatialDatasetServiceSetting(
                name='main_geoserver',
                description='spatial dataset service for app to use',
                engine=SpatialDatasetServiceSetting.GEOSERVER,
                required=True,
            ),
        )

        return sds_settings
