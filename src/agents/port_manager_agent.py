from typing import Sequence

from spade.template import Template

from src.agents.base_agent import BaseAgent
from src.behaviours.request_initiator import RequestInitiator
from src.behaviours.request_responder import RequestResponder
from src.ontology.ontology import ContentElement
from src.ontology.port_terminal_ontology import ContainersDeallocationRequest, DeallocationRequest, PortTerminalOntology
from src.utils.acl_message import ACLMessage
from src.utils.performative import Performative


class DeallocationInitiator(RequestInitiator):
    def __init__(self, container_jid: str):
        super().__init__()
        self._container_jid = container_jid

    async def prepare_requests(self) -> Sequence[ACLMessage]:
        request = ACLMessage(to=self._container_jid)
        request.performative = Performative.REQUEST
        request.protocol = 'Request'
        request.ontology = self.agent.ontology.name
        deallocation_request = DeallocationRequest(self._container_jid)
        self.agent.content_manager.fill_content(deallocation_request, request)
        return [request]


class ContainersDeallocationResponder(RequestResponder):
    async def prepare_response(self, request: ACLMessage) -> ACLMessage:
        content: ContentElement = self.agent.content_manager.extract_content(request)
        if isinstance(content, ContainersDeallocationRequest):
            return request.create_reply(Performative.AGREE)
        return request.create_reply(Performative.NOT_UNDERSTOOD)

    async def prepare_result_notification(self, request: ACLMessage) -> ACLMessage:
        content: ContainersDeallocationRequest = self.agent.content_manager.extract_content(request)

        deallocation_mt = Template()
        deallocation_mt.set_metadata('protocol', 'Request')
        deallocation_mt.set_metadata('action', DeallocationRequest.__key__)

        for container_jid in content.containers_jids:
            deallocation_behaviour = DeallocationInitiator(container_jid)
            self.agent.add_behaviour(deallocation_behaviour, deallocation_mt)
            await deallocation_behaviour.join()

        self.agent.log('Containers deallocated by Port Manager')
        response = ACLMessage(to=str(request.sender))
        response.performative = Performative.INFORM
        response.protocol = 'Request'
        response.ontology = self.agent.ontology.name
        response.action = ContainersDeallocationRequest.__key__
        return response


class PortManagerAgent(BaseAgent):
    def __init__(self, jid: str, password: str):
        super().__init__(jid, password, PortTerminalOntology.instance())

    async def setup(self):
        containers_deallocation_mt = Template()
        containers_deallocation_mt.set_metadata('protocol', 'Request')
        containers_deallocation_mt.set_metadata('action', ContainersDeallocationRequest.__key__)
        self.add_behaviour(ContainersDeallocationResponder(), containers_deallocation_mt)
