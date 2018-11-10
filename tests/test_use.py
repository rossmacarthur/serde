from uuid import UUID, uuid4

from serde import Bool, Dict, Field, Float, Int, List, Model, Nested, Str, Tuple


def test_base_0():

    class MyUuid(Field):

        def serialize(self, value):
            return str(value)

        def deserialize(self, value):
            return UUID(value)

        def validate(self, value):
            assert isinstance(value, UUID)

    class Player(Model):
        key = MyUuid(required=False, default=uuid4)
        name = Tuple(Str, Str)
        age = Int()
        rating = Float()

    class Game(Model):
        finished = Bool()
        players = List(Player)
        board = Dict(Str, Int)

    # Create a player manually
    player = Player(name=('James', 'Williams'), age=23, rating=52.3)

    assert isinstance(player.key, UUID)
    assert player.name == ('James', 'Williams')
    assert player.age == 23
    assert player.rating == 52.3

    # Deserialize a Game from JSON
    json = """{
    "board": {
        "BC": 0,
        "BL": 0,
        "BR": 0,
        "CC": 1,
        "CL": 0,
        "CR": 0,
        "TC": 0,
        "TL": -1,
        "TR": 0
    },
    "finished": false,
    "players": [
        {
            "age": 51,
            "key": "5a47a83b-72d3-4231-b8f6-3c21b635782c",
            "name": [
                "John",
                "Smith"
            ],
            "rating": 65.2
        },
        {
            "age": 43,
            "key": "4f24e615-f4dd-4e69-b2dc-76392e2b1763",
            "name": [
                "Mary",
                "Jones"
            ],
            "rating": 71.0
        }
    ]
}"""

    game = Game.from_json(json)

    assert game.finished is False

    assert game.players[0].key == UUID('5a47a83b-72d3-4231-b8f6-3c21b635782c')
    assert game.players[0].name == ('John', 'Smith')
    assert game.players[0].age == 51
    assert game.players[0].rating == 65.2

    assert game.players[1].key == UUID('4f24e615-f4dd-4e69-b2dc-76392e2b1763')
    assert game.players[1].name == ('Mary', 'Jones')
    assert game.players[1].age == 43
    assert game.players[1].rating == 71.0

    assert game.board == {'TL': -1, 'TC': 0, 'TR': 0,
                          'CL': 0, 'CC': 1, 'CR': 0,
                          'BL': 0, 'BC': 0, 'BR': 0}

    assert game.to_json(indent=4, sort_keys=True) == json


def test_base_1():
    class Address(Model):
        email = Str()

    class User(Model):
        name = Str(rename='username', serializers=[lambda s: s.strip()])
        age = Int(required=False)
        addresses = List(Address, required=False)

    # Serialization
    user = User(name='John Smith', age=53, addresses=[Address(email='john@smith.com')])
    assert user.to_dict() == {'username': 'John Smith',
                              'age': 53,
                              'addresses': [{'email': 'john@smith.com'}]}

    # Deserialization
    user = User.from_dict({'username': 'John Smith',
                           'age': 53,
                           'addresses': [{'email': 'john@smith.com'}]})
    assert user.name == 'John Smith'
    assert user.age == 53
    assert user.addresses == [Address(email='john@smith.com')]


def test_base_2():
    class Version(Model):
        major = Int()
        minor = Int()
        patch = Int(required=False, default=0)

    class Package(Model):
        name = Str(rename='packageName')
        version = Nested(Version)

    # Create an instance of the Model
    package = Package(name='requests', version=Version(2, 19, 1))
    assert package.name == 'requests'
    assert package.version.major == 2
    assert package.version.minor == 19
    assert package.version.patch == 1

    # Serialize the Model as a dictionary
    assert package.to_dict() == {
        'packageName': 'requests',
        'version': {
            'major': 2,
            'minor': 19,
            'patch': 1
        }
    }

    # Deserialize another Model from a dictionary
    package = Package.from_dict({
        'packageName': 'click',
        'version': {
            'major': 7,
            'minor': 0
        }
    })
    assert package.name == 'click'
    assert package.version.major == 7
    assert package.version.minor == 0
    assert package.version.patch == 0
