import asyncio
import uuid
from pprint import pprint
from typing import Sequence

from spade.behaviour import OneShotBehaviour
from spade.message import Message

from src.agents.DFAgent import HandleRegisterRequestBehaviour, HandleSearchBehaviour, \
    HandleDeregisterRequestBehaviour, DFAgentDescription, DFService, DFAgent
from src.agents.base_agent import BaseAgent
from src.ontology.directory_facilitator_ontology import ServiceDescription
from src.utils.content_language import ContentLanguage
from src.utils.interaction_protocol import InteractionProtocol
from src.utils.jid_utils import jid_to_str

XMPP_SERVER = 'host.docker.internal'


class ServiceAgent(BaseAgent):
    class RegistrationHandler(HandleRegisterRequestBehaviour):

        async def handleFailure(self, result: Message):
            print(f"[{jid_to_str(self.agent.jid)}] Registration failure")

        async def handleAccept(self, result: Message):
            print(f"[{jid_to_str(self.agent.jid)}] Registered service")

    class DeregisterHandler(HandleDeregisterRequestBehaviour):

        async def handleAccept(self, result: Message):
            print(f"[{jid_to_str(self.agent.jid)}] Deregistered service")

        async def handleFailure(self, result: Message):
            print(f"[{jid_to_str(self.agent.jid)}] Deregistration failure")

    class JobBehaviour(OneShotBehaviour):
        async def run(self):
            # create service description as str: key, object: value pairs
            serviceDescription: ServiceDescription = ServiceDescription(
                {
                    "type": "ExampleExistingService"
                })

            # create df agent description
            # agentName: str
            # interactionProtocol: str
            # ontology: str
            # language: str
            # services: ServiceDescription
            dfd: DFAgentDescription = DFAgentDescription(
                jid_to_str(self.agent.jid),
                InteractionProtocol.FIPA_QUERY,
                "Ontology",
                ContentLanguage.XML,
                serviceDescription)

            # register service
            await DFService.register(self.agent, dfd, ServiceAgent.RegistrationHandler(), XMPP_SERVER)
            # wait
            await asyncio.sleep(20)
            # deregister service
            await DFService.deregister(self.agent, dfd, ServiceAgent.DeregisterHandler(), XMPP_SERVER)

    async def setup(self):
        b = self.JobBehaviour()
        self.add_behaviour(b)


class ClientAgent(BaseAgent):
    class SearchHandler(HandleSearchBehaviour):

        async def handleResponse(self, result: Sequence[DFAgentDescription]):
            print(
                f'[{jid_to_str(self.agent.jid)}] Search result ({len(result) if result is not None else 0}):')
            pprint(None if result is None else [x.agentName for x in result])

        async def handleFailure(self, result: Message):
            print(f"[{jid_to_str(self.agent.jid)}] Search failure")

    class JobBehaviour(OneShotBehaviour):
        async def run(self):
            serviceDescription: ServiceDescription = ServiceDescription(
                {
                    "type": "ExampleExistingService"
                })

            # searching only by service description
            dfd: DFAgentDescription = DFAgentDescription(
                "",
                "",
                "",
                "",
                serviceDescription)
            await asyncio.sleep(5)
            await DFService.search(self.agent, dfd, ClientAgent.SearchHandler(), XMPP_SERVER)
            await asyncio.sleep(10)
            await DFService.search(self.agent, dfd, ClientAgent.SearchHandler(), XMPP_SERVER)
            await asyncio.sleep(10)
            await DFService.search(self.agent, dfd, ClientAgent.SearchHandler(), XMPP_SERVER)

    async def setup(self):
        b = self.JobBehaviour()
        self.add_behaviour(b)


class OtherServiceAgent(BaseAgent):
    class RegistrationHandler(HandleRegisterRequestBehaviour):

        async def handleFailure(self, result: Message):
            print(f"[{jid_to_str(self.agent.jid)}] Registration failure")

        async def handleAccept(self, result: Message):
            print(f"[{jid_to_str(self.agent.jid)}] Registered service")

    class DeregisterHandler(HandleDeregisterRequestBehaviour):

        async def handleAccept(self, result: Message):
            print(f"[{jid_to_str(self.agent.jid)}] Deregistered service")

        async def handleFailure(self, result: Message):
            print(f"[{jid_to_str(self.agent.jid)}] Deregistration failure")

    class JobBehaviour(OneShotBehaviour):
        async def run(self):
            # create service description as str: key, object: value pairs
            serviceDescription: ServiceDescription = ServiceDescription(
                {
                    "type": "ExampleNotInterestingService"
                })

            # create df agent description
            # agentName: str
            # interactionProtocol: str
            # ontology: str
            # language: str
            # services: ServiceDescription
            dfd: DFAgentDescription = DFAgentDescription(
                jid_to_str(self.agent.jid),
                InteractionProtocol.FIPA_QUERY,
                "Ontology",
                ContentLanguage.XML,
                serviceDescription)

            # register service
            await DFService.register(self.agent, dfd, ServiceAgent.RegistrationHandler(), XMPP_SERVER)
            # wait
            await asyncio.sleep(20)
            # deregister service
            await DFService.deregister(self.agent, dfd, ServiceAgent.DeregisterHandler(), XMPP_SERVER)

    async def setup(self):
        b = self.JobBehaviour()
        self.add_behaviour(b)


if __name__ == "__main__":
    # create DF agent
    df = DFAgent(f'DFagent@{XMPP_SERVER}', 'password1234')
    future = df.start()
    future.result()
    # initialize DFService
    DFService.init(df)

    serviceOtherAgent = OtherServiceAgent(f'otherServiceExample-{str(uuid.uuid1())}@{XMPP_SERVER}', 'password1234')
    future = serviceOtherAgent.start()
    service1Agent = ServiceAgent(f'serviceExample-{str(uuid.uuid1())}@{XMPP_SERVER}', 'password1234')
    future = service1Agent.start()
    asyncio.run(asyncio.sleep(10))
    service2Agent = ServiceAgent(f'serviceExample-{str(uuid.uuid1())}@{XMPP_SERVER}', 'password1234')
    future = service2Agent.start()

    customer = ClientAgent(f'customerExample-{str(uuid.uuid1())}@{XMPP_SERVER}', 'password1234')
    future = customer.start()
