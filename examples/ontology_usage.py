from dataclasses import dataclass

from src.ontology.content_manager import ContentManager
from src.ontology.ontology import Ontology, ContentElement
from src.utils.acl_message import ACLMessage
from src.utils.nested_dataclass import nested_dataclass
from src.utils.singleton import Singleton


# Define custom ontology
@dataclass
class Author(ContentElement):
    first_name: str
    last_name: str
    __key__ = 'author'


@nested_dataclass
class Book(ContentElement):
    title: str
    author: Author
    pages_count: int
    __key__ = 'book'


@Singleton
class BookShopOntology(Ontology):
    def __init__(self):
        super().__init__('Book Shop Ontology')
        self.add(Author)
        self.add(Book)


# Create content manager and register ontology
content_manager = ContentManager()
book_shop_ontology = BookShopOntology.instance()
content_manager.register_ontology(book_shop_ontology)

# Test book serialization and deserialization
book: Book = Book('4.50 from Paddington', Author('Agatha', 'Christie'), 150)
print(f'Initial book object:\n{book}\n')

msg: ACLMessage = ACLMessage(
    to='receiver@host',
    sender='sender@host',
)
msg.ontology = book_shop_ontology.name
content_manager.fill_content(book, msg)
print(f'Book as message body:\n{msg.body}\n')

received_book = content_manager.extract_content(msg)
print(f'Received book object:\n{received_book}\n')
