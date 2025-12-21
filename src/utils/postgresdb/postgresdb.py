from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from src.models import EmbeddedMetadata
from typing import List

class PostgresDB:
    def __init__(self):
        self.engine = None
        self.async_session = None
    
    def connect(self, user: str, password: str, host: str, port: int, database: str):
        '''
        Connect to the PostgreSQL database.
                
        :param self: Instance of the class
        :param user: Database user
        :type user: str
        :param password: Database password
        :type password: str
        :param host: Database host address
        :type host: str
        :param port: Database port number
        :type port: int
        :param database: Database name
        :type database: str
        '''
        connection_string = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
        self.engine = create_async_engine(connection_string)
        self.async_session = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
    
    async def insert(self, data: List[EmbeddedMetadata]):
        '''
        Insert multiple EmbeddedMetadata records into the database.
        
        :param self: Instance of the class
        :param data: List of EmbeddedMetadata instances to insert
        :type data: List[EmbeddedMetadata]
        '''
        retval = False
        try:
            async with self.async_session() as session:
                session.add_all(data)
                await session.commit()
                retval = True
        except Exception as e:
            await session.rollback()
            print(f"Error inserting data: {e}")
        finally:
            return retval
    
    async def update(self, record_id: int, new_data: dict):
        '''
        Update an EmbeddedMetadata record in the database.
        
        :param self: Instance of the class
        :param record_id: ID of the record to update
        :type record_id: int
        :param new_data: Dictionary of fields to update with their new values
        :type new_data: dict
        '''
        retval = False
        try:
            async with self.async_session() as session:
                result = await session.get(EmbeddedMetadata, record_id)
                if result:
                    for key, value in new_data.items():
                        setattr(result, key, value)
                    await session.commit()
                    retval = True
            return retval
        
        except Exception as e:
            await session.rollback()
            print(f"Error updating data: {e}")
    
    async def delete(self, record_id: int):
        '''
        Delete an EmbeddedMetadata record from the database.
        
        :param self: Instance of the class
        :param record_id: ID of the record to delete
        :type record_id: int
        '''
        retval = False
        try:
            async with self.async_session() as session:
                result = await session.get(EmbeddedMetadata, record_id)
                if result:
                    await session.delete(result)
                    await session.commit()
                    retval = True
            return retval
        
        except Exception as e:
            await session.rollback()
            print(f"Error deleting data: {e}")
    
    async def fetch_all(self, filter: EmbeddedMetadata = None) -> List[EmbeddedMetadata]:
        '''
        Fetch all EmbeddedMetadata records from the database.
        :param self: Instance of the class
        :param filter: Optional filter criteria as an EmbeddedMetadata instance
        :type filter: EmbeddedMetadata
        :return: List of EmbeddedMetadata instances
        :rtype: List[EmbeddedMetadata]
        '''
        results = []
        try:
            stmt = None
            if filter:
                query = select(EmbeddedMetadata).where(
                    *(getattr(EmbeddedMetadata, key) == value for key, value in filter.to_dict().items() if value is not None)
                )
            else:
                query = select(EmbeddedMetadata).where(True)
            async with self.async_session() as session:
                results = await session.execute(query)
                results = results.scalars().all()
        except Exception as e:
            print(f"Error fetching data: {e}")
        return results
    
    async def close(self):
        '''
        Close the database connection.
        
        :param self: Instance of the class
        '''
        if self.engine:
            await self.engine.dispose()
        self.async_session = None
