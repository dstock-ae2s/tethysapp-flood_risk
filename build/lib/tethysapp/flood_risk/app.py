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
                name='building',
                url='building',
                controller='flood_risk.controllers.building'
            ),
            UrlMap(
                name='street',
                url='street',
                controller='flood_risk.controllers.street'
            ),
            UrlMap(
                name='manhole',
                url='manhole',
                controller='flood_risk.controllers.manhole'
            ),
            UrlMap(
                name='pipe',
                url='pipe',
                controller='flood_risk.controllers.pipe'
            ),
            UrlMap(
                name='building_process_ajax',
                url='flood-risk/building/building-process-ajax',
                controller='flood_risk.ajax_controllers.building_process'
            ),
            UrlMap(
                name='streets_process_ajax',
                url='flood-risk/street/streets-process-ajax',
                controller='flood_risk.ajax_controllers.streets_process'
            ),
            UrlMap(
                name='manhole_process_ajax',
                url='flood-risk/manhole/manhole-process-ajax',
                controller='flood_risk.ajax_controllers.manhole_process'
            ),
            UrlMap(
                name='pipe_process_ajax',
                url='flood-risk/pipe/pipe-process-ajax',
                controller='flood_risk.ajax_controllers.pipe_process'
            ),
            UrlMap(
                name='file-upload',
                url='flood-risk/building/file-upload',
                controller='flood_risk.ajax_controllers.file_upload'
            ),
            UrlMap(
                name='file-upload-move-files',
                url='flood-risk/building/file-upload-move-files',
                controller='flood_risk.ajax_controllers.file_upload_move_files'
            ),
            UrlMap(
                name='file-upload',
                url='flood-risk/street/file-upload',
                controller='flood_risk.ajax_controllers.file_upload'
            ),
            UrlMap(
                name='file-upload',
                url='flood-risk/manhole/file-upload',
                controller='flood_risk.ajax_controllers.file_upload'
            ),
            UrlMap(
                name='file-upload-move-files',
                url='flood-risk/manhole/file-upload-move-files',
                controller='flood_risk.ajax_controllers.file_upload_move_files'
            ),
            UrlMap(
                name='file-upload',
                url='flood-risk/pipe/file-upload',
                controller='flood_risk.ajax_controllers.file_upload'
            ),
            UrlMap(
                name='file-upload-move-files',
                url='flood-risk/pipe/file-upload-move-files',
                controller='flood_risk.ajax_controllers.file_upload_move_files'
            ),
            UrlMap(
                name='file-upload-move-files',
                url='flood-risk/street/file-upload-move-files',
                controller='flood_risk.ajax_controllers.file_upload_move_files'
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
