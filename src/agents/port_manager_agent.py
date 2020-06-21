from typing import Sequence

from spade.template import Template

from src.agents.base_agent import BaseAgent
from src.behaviours.request_initiator import RequestInitiator
from src.behaviours.request_responder import RequestResponder
from src.ontology.ontology import ContentElement
from src.ontology.port_terminal_ontology import ContainersDeallocationRequest, DeallocationRequest
from src.utils.acl_message import ACLMessage
from src.utils.performative import Performative


class DeallocationInitiator(RequestInitiator):
    def __init__(self, containers_jids: Sequence[str]):
        super().__init__()
        self._containers_jids = containers_jids

    async def prepare_requests(self) -> Sequence[ACLMessage]:
        return [self._create_request(container_jid) for container_jid in self._containers_jids]

    def _create_request(self, container_jid):
        request = ACLMessage(to=container_jid)
        request.performative = Performative.REQUEST
        request.protocol = 'Request',
        request.ontology = self.agent.ontology.name
        deallocation_request = DeallocationRequest(container_jid)
        self.agent.content_manager.fill_content(deallocation_request, request)
        return request


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
        deallocation_behaviour = DeallocationInitiator(content.containers_jids)
        self.agent.add_behaviour(deallocation_behaviour, deallocation_mt)
        await deallocation_behaviour.join()

        self.agent.log('Containers deallocated by Port Manager')
        response = ACLMessage(to=str(request.sender))
        response.performative = Performative.INFORM
        response.protocol = 'Request',
        response.ontology = self.agent.ontology.name
        response.action = ContainersDeallocationRequest.__key__
        return response


class PortManagerAgent(BaseAgent):
    def setup(self):
        containers_deallocation_mt = Template()
        containers_deallocation_mt.set_metadata('protocol', 'Request')
        containers_deallocation_mt.set_metadata('action', ContainersDeallocationRequest.__key__)
        self.add_behaviour(ContainersDeallocationResponder(), containers_deallocation_mt)
