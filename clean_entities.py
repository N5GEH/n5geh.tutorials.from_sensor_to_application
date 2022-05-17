from filip.models.base import FiwareHeader
from filip.utils.cleanup import clear_context_broker, clear_iot_agent

CB_URL = "http://localhost:1026"
IOTA_URL = "http://localhost:4041"
QL_URL = "http://localhost:8668"
# FIWARE-Service
SERVICE = 'controller'
# FIWARE-Servicepath
SERVICE_PATH = '/'
fiware_header = FiwareHeader(service=SERVICE,
                             service_path=SERVICE_PATH)


clear_iot_agent(url=IOTA_URL, fiware_header=fiware_header)
clear_context_broker(url=CB_URL, fiware_header=fiware_header)