import pytest
import aiosqlite

@pytest.fixture
async def in_memory_db():
    """Fixture providing an async connection to an in-memory database."""
    async with aiosqlite.connect(":memory:") as db:
        yield db

@pytest.mark.asyncio
async def test_create_table_in_memory(in_memory_db):
    """Test that creating a table works on an in-memory SQLite connection."""
    await in_memory_db.execute("""
        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)
    await in_memory_db.commit()
    
    # Verify the table exists
    cursor = await in_memory_db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'"
    )
    result = await cursor.fetchone()
    assert result is not None
    assert result[0] == "test_table"

@pytest.mark.asyncio
async def test_insert_and_fetch_row(in_memory_db):
    """Test that inserting and fetching data returns the correct row."""
    await in_memory_db.execute("CREATE TABLE users (id INTEGER, name TEXT)")
    await in_memory_db.execute("INSERT INTO users VALUES (?, ?)", (1, "Alice"))
    await in_memory_db.commit()
    
    cursor = await in_memory_db.execute("SELECT name FROM users WHERE id = 1")
    result = await cursor.fetchone()
    
    assert result is not None
    assert result[0] == "Alice"

@pytest.mark.asyncio
async def test_table_isolation():
    """Test that two separate in-memory DB connections do not share tables."""
    async with aiosqlite.connect(":memory:") as db1:
        await db1.execute("CREATE TABLE isolated (id INTEGER)")
        await db1.commit()
        
        async with aiosqlite.connect(":memory:") as db2:
            # The second connection should not see the first's table
            with pytest.raises(aiosqlite.OperationalError):
                await db2.execute("SELECT * FROM isolated")

@pytest.mark.asyncio
async def test_create_table_if_not_exists(in_memory_db):
    """Test that executing CREATE TABLE IF NOT EXISTS twice does not raise an error."""
    create_stmt = "CREATE TABLE IF NOT EXISTS dummy (id INTEGER)"
    
    # First time creates it
    await in_memory_db.execute(create_stmt)
    await in_memory_db.commit()
    
    # Second time should do nothing and not raise an error
    await in_memory_db.execute(create_stmt)
    await in_memory_db.commit()
    
    # Verify we can still query it
    cursor = await in_memory_db.execute("SELECT * FROM dummy")
    assert await cursor.fetchall() == []

@pytest.mark.asyncio
async def test_invalid_sql_raises_error(in_memory_db):
    """Test that executing invalid SQL syntax raises an OperationalError."""
    with pytest.raises(aiosqlite.OperationalError):
        await in_memory_db.execute("CREATE TABLE BROKEN SYNTAX (id INTEGER)")
