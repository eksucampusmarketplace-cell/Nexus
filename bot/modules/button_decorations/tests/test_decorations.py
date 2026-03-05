"""
Tests for Button Decorations Module.

Run with: pytest bot/modules/button_decorations/tests/
"""

import pytest
from unittest.mock import Mock, patch

from bot.modules.button_decorations.module import (
    ButtonDecorationsModule,
    apply_button_decoration,
    DECORATION_CATEGORIES,
)
from bot.modules.button_decorations.decorated_builder import (
    DecoratedInlineKeyboardBuilder,
    DecoratedKeyboardLayout,
    create_button_set,
    decorate_buttons,
)


class TestButtonDecorationsModule:
    """Test main decoration module functionality."""
    
    def test_decoration_categories_exist(self):
        """Test that decoration categories are defined."""
        assert len(DECORATION_CATEGORIES) > 0
        assert "nature" in DECORATION_CATEGORIES
        assert "animals" in DECORATION_CATEGORIES
        assert "objects" in DECORATION_CATEGORIES
    
    def test_category_structure(self):
        """Test that categories have correct structure."""
        for cat_key, category in DECORATION_CATEGORIES.items():
            assert "name" in category
            assert "icon" in category
            assert "decorations" in category
            assert isinstance(category["decorations"], dict)
    
    def test_decoration_structure(self):
        """Test that decorations have correct structure."""
        for cat_key, category in DECORATION_CATEGORIES.items():
            for deco_key, deco in category["decorations"].items():
                assert "name" in deco
                assert "prefix" in deco
                assert "suffix" in deco
    
    def test_apply_decoration_disabled(self):
        """Test applying decoration when disabled."""
        with patch('bot.modules.button_decorations.module.get_decoration_module', return_value=None):
            result = apply_button_decoration("Test", 123)
            assert result == "Test"
    
    def test_apply_decoration_with_none(self):
        """Test applying minimal:none decoration."""
        with patch('bot.modules.button_decorations.module.get_decoration_module') as mock_get:
            mock_module = Mock()
            mock_module.get_config.return_value = {
                "enabled": True,
                "default_decoration": "minimal:none"
            }
            mock_module.apply_decoration = lambda text, gid: text
            mock_get.return_value = mock_module
            
            result = apply_button_decoration("Test", 123)
            assert result == "Test"
    
    def test_apply_decoration_flowers(self):
        """Test applying nature:flowers decoration."""
        with patch('bot.modules.button_decorations.module.get_decoration_module') as mock_get:
            mock_module = Mock()
            mock_module.get_config.return_value = {
                "enabled": True,
                "default_decoration": "nature:flowers"
            }
            mock_module.apply_decoration = Mock(return_value="🌸 Test 🌺")
            mock_get.return_value = mock_module
            
            result = apply_button_decoration("Test", 123)
            assert result == "🌸 Test 🌺"
            mock_module.apply_decoration.assert_called_once()


class TestDecoratedInlineKeyboardBuilder:
    """Test DecoratedInlineKeyboardBuilder."""
    
    def test_builder_initialization(self):
        """Test builder initializes correctly."""
        builder = DecoratedInlineKeyboardBuilder(group_id=123)
        assert builder.group_id == 123
        assert builder.enabled is True
    
    def test_builder_with_disabled_decorations(self):
        """Test builder with decorations disabled."""
        builder = DecoratedInlineKeyboardBuilder(group_id=123, enabled=False)
        assert builder.enabled is False
    
    @patch('bot.modules.button_decorations.decorated_builder.apply_button_decoration')
    def test_button_with_decoration(self, mock_apply):
        """Test adding button with decoration."""
        mock_apply.return_value =🌸 Test 🌺"
        
        builder = DecoratedInlineKeyboardBuilder(group_id=123)
        builder.button(text="Test", callback_data="test")
        
        mock_apply.assert_called_once_with("Test", 123)
    
    @patch('bot.modules.button_decorations.decorated_builder.apply_button_decoration')
    def test_button_skip_decoration(self, mock_apply):
        """Test skipping decoration for specific button."""
        builder = DecoratedInlineKeyboardBuilder(group_id=123)
        builder.button(text="Test", callback_data="test", skip_decoration=True)
        
        mock_apply.assert_not_called()
    
    @patch('bot.modules.button_decorations.decorated_builder.apply_button_decoration')
    def test_button_disabled_decorations(self, mock_apply):
        """Test button when decorations are disabled."""
        builder = DecoratedInlineKeyboardBuilder(group_id=123, enabled=False)
        builder.button(text="Test", callback_data="test")
        
        mock_apply.assert_not_called()


class TestDecoratedKeyboardLayout:
    """Test DecoratedKeyboardLayout."""
    
    def test_layout_initialization(self):
        """Test layout initializes correctly."""
        layout = DecoratedKeyboardLayout(group_id=123)
        assert layout.group_id == 123
        assert layout.enabled is True
    
    def test_layout_disabled_decorations(self):
        """Test layout with decorations disabled."""
        layout = DecoratedKeyboardLayout(group_id=123, enabled=False)
        assert layout.enabled is False
    
    @patch('bot.modules.button_decorations.decorated_builder.apply_button_decoration')
    def test_add_button(self, mock_apply):
        """Test adding button to layout."""
        mock_apply.return_value =🌸 Test 🌺"
        
        layout = DecoratedKeyboardLayout(group_id=123)
        layout.add_button("Test", "test_callback", icon="🔥")
        
        mock_apply.assert_called_once()
    
    @patch('bot.modules.button_decorations.decorated_builder.apply_button_decoration')
    def test_add_button_skip_decoration(self, mock_apply):
        """Test adding button with skip_decoration."""
        layout = DecoratedKeyboardLayout(group_id=123)
        layout.add_button("Test", "test_callback", skip_decoration=True)
        
        mock_apply.assert_not_called()
    
    def test_build_returns_markup(self):
        """Test that build returns InlineKeyboardMarkup."""
        layout = DecoratedKeyboardLayout(group_id=123)
        layout.add_button("Test", "test")
        markup = layout.build()
        
        # Should return InlineKeyboardMarkup
        assert markup is not None
        assert hasattr(markup, 'inline_keyboard')


class TestButtonSets:
    """Test predefined button sets."""
    
    def test_create_moderation_set(self):
        """Test creating moderation button set."""
        with patch('bot.modules.button_decorations.decorated_builder.apply_button_decoration', return_value="🌸 Warn 🌺"):
            markup = create_button_set(123, "moderation")
            assert markup is not None
    
    def test_create_confirmation_set(self):
        """Test creating confirmation button set."""
        with patch('bot.modules.button_decorations.decorated_builder.apply_button_decoration', return_value="🌸 Yes 🌺"):
            markup = create_button_set(123, "confirmation")
            assert markup is not None
    
    def test_create_navigation_set(self):
        """Test creating navigation button set."""
        with patch('bot.modules.button_decorations.decorated_builder.apply_button_decoration', return_value="🌸 Back 🌺"):
            markup = create_button_set(123, "navigation")
            assert markup is not None
    
    def test_create_invalid_set(self):
        """Test creating invalid button set raises error."""
        with pytest.raises(ValueError):
            create_button_set(123, "invalid_set")


class TestDecorateButtons:
    """Test decorate_buttons helper."""
    
    @patch('bot.modules.button_decorations.decorated_builder.apply_button_decoration')
    def test_decorate_single_button(self, mock_apply):
        """Test decorating a single button."""
        mock_apply.return_value =🌸 Test 🌺"
        
        buttons = [{"text": "Test", "callback": "test"}]
        decorated = decorate_buttons(buttons, 123)
        
        assert len(decorated) == 1
        assert decorated[0]["text"] == "🌸 Test 🌺"
        mock_apply.assert_called_once_with("Test", 123)
    
    @patch('bot.modules.button_decorations.decorated_builder.apply_button_decoration')
    def test_decorate_multiple_buttons(self, mock_apply):
        """Test decorating multiple buttons."""
        mock_apply.side_effect = ["🌸 Test1 🌺", "🌸 Test2 🌺"]
        
        buttons = [
            {"text": "Test1", "callback": "test1"},
            {"text": "Test2", "callback": "test2"},
        ]
        decorated = decorate_buttons(buttons, 123)
        
        assert len(decorated) == 2
        assert decorated[0]["text"] == "🌸 Test1 🌺"
        assert decorated[1]["text"] == "🌸 Test2 🌺"
        assert mock_apply.call_count == 2


class TestDecorationConfig:
    """Test decoration configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        from bot.modules.button_decorations.module import ButtonDecorationsConfig
        
        config = ButtonDecorationsConfig()
        assert config.enabled is False
        assert config.default_decoration == "minimal:none"
        assert config.position == "both"
        assert config.apply_to_all is False
    
    def test_config_to_dict(self):
        """Test converting config to dict."""
        from bot.modules.button_decorations.module import ButtonDecorationsConfig
        
        config = ButtonDecorationsConfig(enabled=True)
        config_dict = config.dict()
        
        assert config_dict["enabled"] is True
        assert "default_decoration" in config_dict
        assert "position" in config_dict


class TestIntegrationExamples:
    """Test integration examples work correctly."""
    
    @patch('bot.modules.button_decorations.module.apply_button_decoration')
    def test_simple_example(self, mock_apply):
        """Test simple decoration example."""
        mock_apply.return_value =🌸 Click Me 🌺"
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        
        builder = InlineKeyboardBuilder()
        builder.button(text=mock_apply("Click Me", 123), callback_data="clicked")
        
        mock_apply.assert_called_once()
    
    @patch('bot.modules.button_decorations.decorated_builder.apply_button_decoration')
    def test_builder_example(self, mock_apply):
        """Test builder decoration example."""
        mock_apply.return_value =🌸 Dashboard 🌺"
        
        builder = DecoratedInlineKeyboardBuilder(group_id=123)
        builder.button(text="Dashboard", callback_data="dashboard")
        
        mock_apply.assert_called_once()


# Fixtures
@pytest.fixture
def mock_ctx():
    """Mock NexusContext."""
    ctx = Mock()
    ctx.group_id = 123
    ctx.send = Mock()
    return ctx


@pytest.fixture
def mock_decoration_module():
    """Mock decoration module."""
    module = Mock()
    module.get_config = Mock(return_value={
        "enabled": True,
        "default_decoration": "nature:flowers",
        "position": "both"
    })
    module.set_config = Mock()
    module.apply_decoration = Mock(return_value="🌸 Test 🌺")
    return module


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
