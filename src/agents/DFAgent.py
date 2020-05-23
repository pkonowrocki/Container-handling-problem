import sys
from enum import IntEnum
from typing import Sequence, Optional

from spade.agent import Agent
from spade.behaviour import *

from src.ontology.content_manager import ContentManager
from src.ontology.directory_facilitator_ontology import DFAgentDescription, \
    SearchServiceResponse, RegisterService, DeregisterService, DFOntology, SearchServiceRequest
from src.ontology.ontology import Action
from src.utils.message_utils import *


class DFAgent(Agent):
    class RegisterBehaviour(CyclicBehaviour):
        def __init__(self, registeredServices: Sequence[DFAgentDescription], contentManager: ContentManager):
            super().__init__()
            self.registeredServices: Sequence[DFAgentDescription] = registeredServices
            self.contentManager: ContentManager = contentManager

        async def run(self):
            msg = await self.receive()
            if msg:
                reply: Message = msg.make_reply()
                try:
                    service: RegisterService = self.contentManager.extract_content(msg)
                    self.registeredServices.append(service.request)
                    reply.set_metadata("performative", str(Performative.INFORM.value))
                except Exception as ex:
                    sys.stderr.write(f'DF Agent exception \n {ex} \n at message \n {msg}')
                    reply.set_metadata("performative", str(Performative.FAILURE.value))
                finally:
                    await self.send(reply)

    class SearchBehaviour(CyclicBehaviour):
        def __init__(self, registeredServices: Sequence[DFAgentDescription], contentManager: ContentManager):
            super().__init__()
            self.registeredServices: Sequence[DFAgentDescription] = registeredServices
            self.contentManager: ContentManager = contentManager

        async def run(self):
            msg = await self.receive()
            if msg:
                reply: Message = msg.make_reply()
                try:
                    request: SearchServiceRequest = self.contentManager.extract_content(msg)
                    template: DFAgentDescription = request.request
                    dfAgentDescriptionList: Sequence[DFAgentDescription] = self.__search(template)
                    searchServiceResponse: SearchServiceResponse = SearchServiceResponse(dfAgentDescriptionList)

                    self.contentManager.fill_content(searchServiceResponse, reply)
                    reply.set_metadata("ontology", DFService.DFServiceOntology.name)
                    reply.set_metadata("performative", str(Performative.INFORM.value))
                except Exception as ex:
                    sys.stderr.write(f'DF Agent exception \n {ex} \n at message \n {msg}')
                    reply.set_metadata("performative", str(Performative.FAILURE.value))
                finally:
                    await self.send(reply)

        def __search(self, template: DFAgentDescription) -> Optional[Sequence[DFAgentDescription]]:
            result = []
            for item in self.registeredServices:
                if DFAgent.SearchBehaviour.__compare(item, template):
                    result.append(item)
            return result if not result == [] else None

        @staticmethod
        def __compare(item: DFAgentDescription, template: DFAgentDescription) -> bool:
            if template.agentName is not None and not item.agentName == template.agentName:
                return False
            if template.service is not None and \
                    template.service.properties is not None and \
                    item.service is not None and \
                    item.service.properties is not None and \
                    all(k in item.service.properties.keys() for k in template.service.properties.keys()) and \
                    all(template.service.properties[k] == item.service.properties[k]
                        for k in template.service.properties.keys()):
                return True
            else:
                return False

    class DeleteBehaviour(CyclicBehaviour):
        def __init__(self, registeredServices: Sequence[DFAgentDescription], contentManager: ContentManager):
            super().__init__()
            self.registeredServices: Sequence[DFAgentDescription] = registeredServices
            self.contentManager: ContentManager = contentManager

        async def run(self):
            msg = await self.receive()
            if msg:
                template = self.contentManager.extract_content(msg)
                reply: Message = msg.make_reply()
                try:
                    self.__delete(template.request)
                    reply.set_metadata("performative", str(Performative.INFORM.value))
                except Exception as ex:
                    sys.stderr.write(f'DF Agent exception \n {ex} \n at message \n {msg}')
                    reply.set_metadata("performative", str(Performative.FAILURE.value))
                finally:
                    await self.send(reply)

        def __delete(self, template: DFAgentDescription):
            toBeDeleted = [x for x in self.registeredServices if DFAgent.DeleteBehaviour.__compare(x, template)]
            for item in toBeDeleted:
                self.registeredServices.remove(item)

        @staticmethod
        def __compare(item: DFAgentDescription, template: DFAgentDescription) -> bool:
            if template.agentName is not None and not item.agentName == template.agentName:
                return False
            if template.ontology is not None and not item.ontology == template.ontology:
                return False
            if template.language is not None and not item.language == template.language:
                return False
            if template.interactionProtocol is not None and not item.interactionProtocol == template.interactionProtocol:
                return False
            if template.service is not None and \
                    template.service.properties is not None and \
                    item.service is not None and \
                    item.service.properties is not None and \
                    all(k in item.service.properties.keys() for k in template.service.properties.keys()) and \
                    all(template.service.properties[k] == item.service.properties[k]
                        for k in template.service.properties.keys()):
                return True
            else:
                return False

    """
    Directory Facilitator Agent
    """

    def __init__(self, jid: str, password: str, verify_security: bool = False):
        super().__init__(jid, password, verify_security)
        self.registeredServices: Sequence[DFAgentDescription] = []
        self.contentManager: ContentManager = ContentManager()
        self.dfOntology: DFOntology = DFOntology()
        self.contentManager.register_ontology(self.dfOntology)

    async def setup(self):
        registerTemplate: Template = Template()
        registerTemplate.set_metadata("ontology", self.dfOntology.name)
        registerTemplate.set_metadata("action", RegisterService.__key__)
        self.add_behaviour(self.RegisterBehaviour(self.registeredServices, self.contentManager), registerTemplate)

        searchTemplate: Template = Template()
        searchTemplate.set_metadata("ontology", self.dfOntology.name)
        searchTemplate.set_metadata("action", SearchServiceRequest.__key__)
        self.add_behaviour(self.SearchBehaviour(self.registeredServices, self.contentManager), searchTemplate)

        deregisterTemplate: Template = Template()
        deregisterTemplate.set_metadata("ontology", self.dfOntology.name)
        deregisterTemplate.set_metadata("action", DeregisterService.__key__)
        self.add_behaviour(self.DeleteBehaviour(self.registeredServices, self.contentManager), deregisterTemplate)


class HandlerBehaviour(CyclicBehaviour):
    @abstractmethod
    async def run(self):
        pass

    class CommunicationState(IntEnum):
        SEND_REQUEST = 0
        WAIT_FOR_RESPONSE = 1
        HANDLE = 2
        EMPTY_MESSAGE = 99
        EMPTY_CONTENT_MANAGER = 100
        EMPTY = 101

    def __init__(self):
        super().__init__()
        self.contentManager: Optional[ContentManager] = None
        self.msg: Optional[Message] = None
        self.state: HandlerBehaviour.CommunicationState = HandlerBehaviour.CommunicationState.EMPTY
        self.__setState()

    def __setState(self):
        if self.msg is None and self.contentManager is None:
            self.state = HandlerBehaviour.CommunicationState.EMPTY
        elif self.msg is None:
            self.state = HandlerBehaviour.CommunicationState.EMPTY_MESSAGE
        elif self.contentManager is None:
            self.state = HandlerBehaviour.CommunicationState.EMPTY_CONTENT_MANAGER
        else:
            self.state = HandlerBehaviour.CommunicationState.SEND_REQUEST

    def setMessage(self, msg: Message):
        self.msg = msg
        self.__setState()

    def setContentManager(self, contentManager: ContentManager):
        self.contentManager = contentManager
        self.__setState()


class HandleSearchBehaviour(HandlerBehaviour):
    def __init__(self):
        super().__init__()
        self.result: Optional[Sequence[DFAgentDescription]] = None

    @abstractmethod
    async def handleResponse(self, result: Optional[Sequence[DFAgentDescription]]):
        pass

    @abstractmethod
    async def handleFailure(self, msg: Message):
        pass

    async def run(self):
        if self.state == HandlerBehaviour.CommunicationState.EMPTY_MESSAGE or \
                self.state == HandlerBehaviour.CommunicationState.EMPTY or \
                self.state == HandlerBehaviour.CommunicationState.EMPTY_CONTENT_MANAGER:
            raise Exception(f"Empty {self.state}")
        elif self.state == HandleSearchBehaviour.CommunicationState.SEND_REQUEST:
            if self.msg is not None:
                await self.send(self.msg)
                self.state = HandleSearchBehaviour.CommunicationState.WAIT_FOR_RESPONSE
        elif self.state == HandleSearchBehaviour.CommunicationState.WAIT_FOR_RESPONSE:
            random: Optional[Message] = await self.receive()
            if random is not None and get_ontology(random) == DFService.DFServiceOntology.name and \
                    get_action(random) == SearchServiceResponse.__key__:
                self.result: SearchServiceResponse = self.contentManager.extract_content(random)
                if self.result:
                    if get_performative(random) == Performative.INFORM:
                        await self.handleResponse(self.result.list)
                    elif get_performative(random) == Performative.FAILURE:
                        await self.handleFailure(random)
                    self.kill()


class HandleRegisterRequestBehaviour(HandlerBehaviour):
    def __init__(self):
        super().__init__()
        self.result: Optional[Message] = None

    @abstractmethod
    async def handleAccept(self, result: Message):
        pass

    @abstractmethod
    async def handleFailure(self, result: Message):
        pass

    async def run(self):
        if self.state == HandlerBehaviour.CommunicationState.EMPTY_MESSAGE or \
                self.state == HandlerBehaviour.CommunicationState.EMPTY or \
                self.state == HandlerBehaviour.CommunicationState.EMPTY_CONTENT_MANAGER:
            raise Exception(f"Empty {self.state}")
        elif self.state == HandlerBehaviour.CommunicationState.SEND_REQUEST:
            if self.msg is not None:
                await self.send(self.msg)
                self.state = HandlerBehaviour.CommunicationState.WAIT_FOR_RESPONSE
        elif self.state == HandlerBehaviour.CommunicationState.WAIT_FOR_RESPONSE:
            random: Optional[Message] = await self.receive()
            if random is not None and get_ontology(random) == DFService.DFServiceOntology.name:
                self.result = random
                self.state = HandlerBehaviour.CommunicationState.HANDLE
                if get_performative(self.result) == Performative.INFORM:
                    await self.handleAccept(self.result)
                elif get_performative(self.result) == Performative.FAILURE:
                    await self.handleFailure(self.result)
                self.kill()


class HandleDeregisterRequestBehaviour(HandlerBehaviour):
    def __init__(self):
        super().__init__()
        self.result: Optional[Message] = None

    @abstractmethod
    async def handleAccept(self, result: Message):
        pass

    @abstractmethod
    async def handleFailure(self, result: Message):
        pass

    async def run(self):
        if self.state == HandlerBehaviour.CommunicationState.EMPTY_MESSAGE or \
                self.state == HandlerBehaviour.CommunicationState.EMPTY or \
                self.state == HandlerBehaviour.CommunicationState.EMPTY_CONTENT_MANAGER:
            raise Exception(f"Empty {self.state}")
        elif self.state == HandlerBehaviour.CommunicationState.SEND_REQUEST:
            if self.msg is not None:
                await self.send(self.msg)
                self.state = HandlerBehaviour.CommunicationState.WAIT_FOR_RESPONSE
        elif self.state == HandlerBehaviour.CommunicationState.WAIT_FOR_RESPONSE:
            random: Optional[Message] = await self.receive()
            if random is not None and get_ontology(random) == DFService.DFServiceOntology.name:
                self.result = random
                if get_performative(self.result) == Performative.INFORM:
                    await self.handleAccept(self.result)
                elif get_performative(self.result) == Performative.FAILURE:
                    await self.handleFailure(self.result)
                self.kill()


class DFService:
    __df: DFAgent = None
    __contentManager: ContentManager = None
    DFServiceOntology: DFOntology = None

    @staticmethod
    def init(dfAgent: DFAgent):
        DFService.__df = dfAgent
        DFService.__contentManager = ContentManager()
        DFService.DFServiceOntology = DFOntology()
        DFService.__contentManager.register_ontology(DFService.DFServiceOntology)

    @staticmethod
    async def register(agent: Agent, dfd: DFAgentDescription,
                       handleBehaviour: HandleRegisterRequestBehaviour):
        if dfd is None:
            raise TypeError
        request: Message = DFService.__createRequestMessage(agent, RegisterService(dfd))
        request.set_metadata("action", RegisterService.__key__)
        await DFService.__doFipaRequestClient(agent, request, handleBehaviour)

    @staticmethod
    async def search(agent: Agent, dfd: DFAgentDescription,
                     handleBehaviour: HandleSearchBehaviour):
        if dfd is None:
            raise TypeError
        request: Message = DFService.__createRequestMessage(agent, SearchServiceRequest(dfd))
        request.set_metadata("action", SearchServiceRequest.__key__)
        await DFService.__doFipaRequestClient(agent, request, handleBehaviour)

    @staticmethod
    async def deregister(agent: Agent, dfd: DFAgentDescription,
                         handleBehaviour: HandleDeregisterRequestBehaviour):
        if dfd is None:
            raise TypeError
        request: Message = DFService.__createRequestMessage(agent, DeregisterService(dfd))
        await DFService.__doFipaRequestClient(agent, request, handleBehaviour)

    @staticmethod
    async def __doFipaRequestClient(agent: Agent, request: Message,
                                    handlerBehaviour: HandlerBehaviour):
        handlerBehaviour.setMessage(request)
        handlerBehaviour.setContentManager(DFService.__contentManager)
        agent.add_behaviour(handlerBehaviour)

    @staticmethod
    def __createRequestMessage(agent: Agent, action: Action) -> Message:
        msg: Message = Message(
            to=jid_to_str(DFService.__df.jid),
            sender=jid_to_str(agent.jid)
        )

        msg.set_metadata("performative", str(Performative.REQUEST))
        msg.set_metadata("ontology", DFService.DFServiceOntology.name)
        DFService.__contentManager.fill_content(action, msg)
        return msg
