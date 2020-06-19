from spade.template import Template

from src.agents.base_agent import BaseAgent
from src.behaviours.request_responder import RequestResponder
from src.ontology.port_terminal_ontology import ContainersDeallocationRequest
from src.utils.acl_message import ACLMessage
from src.utils.performative import Performative


class ContainersDeallocationResponder(RequestResponder):
    async def prepare_response(self, request: ACLMessage) -> ACLMessage:
        return request.create_reply(Performative.AGREE)

    async def prepare_result_notification(self, request: ACLMessage) -> ACLMessage:
        # TODO: Add containers deallocation logic here
        self.agent.log('Containers deallocated by Port Manager')
        response = ACLMessage(to=str(request.sender))
        response.performative = Performative.INFORM
        response.protocol = 'Request',
        response.ontology = self.agent.ontology.name
        response.action = ContainersDeallocationRequest.__key__
        return  response


class PortManagerAgent(BaseAgent):
    def setup(self):
        containers_deallocation_mt = Template()
        containers_deallocation_mt.set_metadata('protocol', 'Request')
        containers_deallocation_mt.set_metadata('action', ContainersDeallocationRequest.__key__)
        self.add_behaviour(ContainersDeallocationResponder(), containers_deallocation_mt)
