import sys
from enum import IntEnum
from typing import Sequence, Optional

from spade.agent import Agent
from spade.behaviour import *

from src.ontology.content_manager import ContentManager
from src.ontology.directory_facilitator_ontology import DFAgentDescription, DFAgentDescriptionList, \
    RegisterServiceOntology, DeleteServiceOntology, SearchServiceResponseOntology, SearchServiceRequestOntology
from src.ontology.ontology import Ontology
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
                    service = self.contentManager.extract_content(msg)
                    self.registeredServices.append(service)
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
                    template: DFAgentDescription = self.contentManager.extract_content(msg)
                    dfAgentDescriptionList: DFAgentDescriptionList = self.__search(template)
                    self.contentManager.fill_content(dfAgentDescriptionList, reply)
                    reply.set_metadata("ontology", DFService.searchServiceResponseOntology.name)
                    reply.set_metadata("performative", str(Performative.INFORM.value))
                except Exception as ex:
                    sys.stderr.write(f'DF Agent exception \n {ex} \n at message \n {msg}')
                    reply.set_metadata("performative", str(Performative.FAILURE.value))
                finally:
                    await self.send(reply)

        def __search(self, template: DFAgentDescription) -> DFAgentDescriptionList:
            result = []
            for item in self.registeredServices:
                if DFAgent.SearchBehaviour.__compare(item, template):
                    result.append(item)
            return DFAgentDescriptionList(result if not result == [] else None)

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
        def __init__(self,  registeredServices: Sequence[DFAgentDescription], contentManager: ContentManager):
            super().__init__()
            self. registeredServices: Sequence[DFAgentDescription] = registeredServices
            self.contentManager: ContentManager = contentManager

        async def run(self):
            msg = await self.receive()
            if msg:
                reply: Message = msg.make_reply()
                try:
                    template: DFAgentDescription = self.contentManager.extract_content(msg)
                    self.__delete(template)
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

        self.registerServiceOntology: RegisterServiceOntology = RegisterServiceOntology()
        self.contentManager.register_ontology(self.registerServiceOntology)

        self.searchServiceRequestOntology: SearchServiceRequestOntology = SearchServiceRequestOntology()
        self.contentManager.register_ontology(self.searchServiceRequestOntology)

        self.searchServiceResponseOntology: SearchServiceResponseOntology = SearchServiceResponseOntology()
        self.contentManager.register_ontology(self.searchServiceResponseOntology)

        self.deregisterServiceOntology: DeleteServiceOntology = DeleteServiceOntology()
        self.contentManager.register_ontology(self.deregisterServiceOntology)

    async def setup(self):
        registerTemplate: Template = Template()
        registerTemplate.set_metadata("ontology", self.registerServiceOntology.name)
        self.add_behaviour(self.RegisterBehaviour(self.registeredServices, self.contentManager), registerTemplate)

        searchTemplate: Template = Template()
        searchTemplate.set_metadata("ontology", self.searchServiceRequestOntology.name)
        self.add_behaviour(self.SearchBehaviour(self.registeredServices, self.contentManager), searchTemplate)

        deregisterTemplate: Template = Template()
        deregisterTemplate.set_metadata("ontology", self.deregisterServiceOntology.name)
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
        self.contentManager: ContentManager = None
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
        self.result: Optional[DFAgentDescriptionList] = None

    @abstractmethod
    async def handleResponse(self, result: DFAgentDescriptionList):
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
            if random is not None and get_ontology(random) == DFService.searchServiceResponseOntology.name:
                if get_performative(random) == Performative.INFORM:
                    self.result = self.contentManager.extract_content(random)
                    await self.handleResponse(self.result)
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
            if random is not None and get_ontology(random) == DFService.registerServiceOntology.name:
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
            if random is not None and get_ontology(random) == DFService.deregisterServiceOntology.name:
                self.result = random
                if get_performative(self.result) == Performative.INFORM:
                    await self.handleAccept(self.result)
                elif get_performative(self.result) == Performative.FAILURE:
                    await self.handleFailure(self.result)
                self.kill()


class DFService:
    __df: DFAgent = None
    __contentManager: ContentManager = None
    registerServiceOntology: RegisterServiceOntology = None
    searchServiceRequestOntology: SearchServiceRequestOntology = None
    searchServiceResponseOntology: SearchServiceResponseOntology = None
    deregisterServiceOntology: DeleteServiceOntology = None

    @staticmethod
    def init(dfAgent: DFAgent):
        DFService.__df = dfAgent
        DFService.__contentManager = ContentManager()
        DFService.registerServiceOntology = RegisterServiceOntology()
        DFService.__contentManager.register_ontology(DFService.registerServiceOntology)
        DFService.searchServiceRequestOntology = SearchServiceRequestOntology()
        DFService.__contentManager.register_ontology(DFService.searchServiceRequestOntology)
        DFService.searchServiceResponseOntology = SearchServiceResponseOntology()
        DFService.__contentManager.register_ontology(DFService.searchServiceResponseOntology)
        DFService.deregisterServiceOntology = DeleteServiceOntology()
        DFService.__contentManager.register_ontology(DFService.deregisterServiceOntology)

    @staticmethod
    async def register(agent: Agent, dfd: DFAgentDescription,
                       handleBehaviour: HandleRegisterRequestBehaviour):
        if dfd is None:
            raise TypeError
        request: Message = DFService.__createRequestMessage(agent, dfd, DFService.registerServiceOntology)
        await DFService.__doFipaRequestClient(agent, request, handleBehaviour)

    @staticmethod
    async def search(agent: Agent, dfd: DFAgentDescription,
                     handleBehaviour: HandleSearchBehaviour):
        if dfd is None:
            raise TypeError
        request: Message = DFService.__createRequestMessage(agent, dfd, DFService.searchServiceRequestOntology)
        await DFService.__doFipaRequestClient(agent, request, handleBehaviour)

    @staticmethod
    async def deregister(agent: Agent, dfd: DFAgentDescription,
                         handleBehaviour: HandleDeregisterRequestBehaviour):
        if dfd is None:
            raise TypeError
        request: Message = DFService.__createRequestMessage(agent, dfd, DFService.deregisterServiceOntology)
        await DFService.__doFipaRequestClient(agent, request, handleBehaviour)

    @staticmethod
    async def __doFipaRequestClient(agent: Agent, request: Message,
                                    handlerBehaviour: HandlerBehaviour):
        handlerBehaviour.setMessage(request)
        handlerBehaviour.setContentManager(DFService.__contentManager)
        agent.add_behaviour(handlerBehaviour)

    @staticmethod
    def __createRequestMessage(agent: Agent, dfd: DFAgentDescription, ontology: Ontology) -> Message:
        msg: Message = Message(
            to=jid_to_str(DFService.__df.jid),
            sender=jid_to_str(agent.jid)
        )

        msg.set_metadata("performative", str(Performative.REQUEST))
        msg.set_metadata("ontology", ontology.name)
        msg.set_metadata("language", "XML")
        DFService.__contentManager.fill_content(dfd, msg)
        return msg
