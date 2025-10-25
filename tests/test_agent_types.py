"""
Tests for agent type configurations
"""

import pytest
from aaas.models import (
    AgentType,
    PermissionMode,
    AgentConfig,
    get_agent_config_for_type,
    AGENT_TYPE_CONFIGS,
)


class TestAgentTypeConfigurations:
    """Test agent type configurations"""

    def test_all_agent_types_have_configs(self):
        """Test that all agent types have configurations"""
        for agent_type in AgentType:
            assert agent_type in AGENT_TYPE_CONFIGS, f"Missing config for {agent_type}"

    def test_agent_type_configs_structure(self):
        """Test that all agent type configs have required fields"""
        required_fields = ["description", "system_prompt", "allowed_tools", "permission_mode"]

        for agent_type, config in AGENT_TYPE_CONFIGS.items():
            for field in required_fields:
                assert field in config, f"{agent_type} missing {field}"

    def test_system_prompts_not_empty(self):
        """Test that all system prompts are non-empty"""
        for agent_type, config in AGENT_TYPE_CONFIGS.items():
            assert config["system_prompt"], f"{agent_type} has empty system prompt"
            assert len(config["system_prompt"]) > 10, f"{agent_type} system prompt too short"

    def test_allowed_tools_not_empty(self):
        """Test that all agent types have at least one tool"""
        for agent_type, config in AGENT_TYPE_CONFIGS.items():
            assert config["allowed_tools"], f"{agent_type} has no allowed tools"
            assert isinstance(config["allowed_tools"], list), f"{agent_type} tools not a list"

    def test_permission_modes_valid(self):
        """Test that all permission modes are valid"""
        for agent_type, config in AGENT_TYPE_CONFIGS.items():
            perm_mode = config["permission_mode"]
            assert isinstance(perm_mode, PermissionMode), f"{agent_type} invalid permission mode type"

    def test_research_agent_config(self):
        """Test research agent specific configuration"""
        config = AGENT_TYPE_CONFIGS[AgentType.RESEARCH]

        assert "research" in config["description"].lower()
        assert "research" in config["system_prompt"].lower()
        assert "WebSearch" in config["allowed_tools"] or "WebFetch" in config["allowed_tools"]
        assert config["permission_mode"] == PermissionMode.ACCEPT_EDITS

    def test_code_agent_config(self):
        """Test code agent specific configuration"""
        config = AGENT_TYPE_CONFIGS[AgentType.CODE]

        assert "code" in config["description"].lower()
        assert "code" in config["system_prompt"].lower()
        assert "Write" in config["allowed_tools"]
        assert "Edit" in config["allowed_tools"]
        assert config["permission_mode"] == PermissionMode.ACCEPT_EDITS

    def test_customer_support_no_bash(self):
        """Test that customer support agent doesn't have Bash access"""
        config = AGENT_TYPE_CONFIGS[AgentType.CUSTOMER_SUPPORT]

        assert "Bash" not in config["allowed_tools"], "Customer support should not have Bash access"
        assert config["permission_mode"] == PermissionMode.ASK, "Customer support should require approval"

    def test_finance_agent_safe_config(self):
        """Test finance agent has appropriate security settings"""
        config = AGENT_TYPE_CONFIGS[AgentType.FINANCE]

        assert config["permission_mode"] == PermissionMode.ASK, "Finance agent should require approval"
        assert "finance" in config["system_prompt"].lower()

    def test_get_agent_config_for_type(self):
        """Test getting agent config for a type"""
        config = get_agent_config_for_type(AgentType.RESEARCH)

        assert config["description"]
        assert config["system_prompt"]
        assert config["allowed_tools"]
        assert config["permission_mode"]

    def test_get_agent_config_with_custom_override(self):
        """Test that custom config can override base config"""
        custom_config = AgentConfig(
            agent_type=AgentType.GENERAL,
            system_prompt="Custom system prompt",
            allowed_tools=["Read", "Write"],
            permission_mode=PermissionMode.ACCEPT_ALL,
        )

        config = get_agent_config_for_type(AgentType.GENERAL, custom_config)

        assert config["system_prompt"] == "Custom system prompt"
        assert config["allowed_tools"] == ["Read", "Write"]
        assert config["permission_mode"] == PermissionMode.ACCEPT_ALL

    def test_agent_config_backward_compatibility(self):
        """Test backward compatibility with template field"""
        config = AgentConfig(template="research-agent")

        assert config.template == "research-agent"
        # Template doesn't automatically set agent_type, that's done in AgentManager

    def test_agent_type_enum_values(self):
        """Test that all agent type enum values are strings"""
        for agent_type in AgentType:
            assert isinstance(agent_type.value, str)
            assert agent_type.value.islower() or "_" in agent_type.value

    def test_permission_mode_enum_values(self):
        """Test permission mode enum values"""
        assert PermissionMode.ASK.value == "ask"
        assert PermissionMode.ACCEPT_EDITS.value == "acceptEdits"
        assert PermissionMode.ACCEPT_ALL.value == "acceptAll"


class TestAgentTypeSpecializations:
    """Test agent type specializations"""

    def test_research_agent_has_search_tools(self):
        """Research agent should have search capabilities"""
        config = AGENT_TYPE_CONFIGS[AgentType.RESEARCH]

        search_tools = {"WebSearch", "WebFetch", "Grep", "Glob"}
        has_search = any(tool in config["allowed_tools"] for tool in search_tools)

        assert has_search, "Research agent should have search tools"

    def test_code_agent_has_file_tools(self):
        """Code agent should have file manipulation tools"""
        config = AGENT_TYPE_CONFIGS[AgentType.CODE]

        file_tools = {"Read", "Write", "Edit"}
        has_file_tools = all(tool in config["allowed_tools"] for tool in file_tools)

        assert has_file_tools, "Code agent should have all file manipulation tools"

    def test_data_analysis_agent_has_bash(self):
        """Data analysis agent should have Bash for data processing"""
        config = AGENT_TYPE_CONFIGS[AgentType.DATA_ANALYSIS]

        assert "Bash" in config["allowed_tools"], "Data analysis agent needs Bash for processing"

    def test_personal_assistant_restricted_tools(self):
        """Personal assistant should have restricted tool access"""
        config = AGENT_TYPE_CONFIGS[AgentType.PERSONAL_ASSISTANT]

        # Should not have dangerous tools
        assert "Bash" not in config["allowed_tools"], "Personal assistant shouldn't have Bash"

        # Should have basic tools
        assert "Read" in config["allowed_tools"]
        assert "Write" in config["allowed_tools"]


class TestAgentConfigValidation:
    """Test agent configuration validation"""

    def test_valid_agent_config(self):
        """Test creating valid agent config"""
        config = AgentConfig(
            agent_type=AgentType.CODE,
            language="en",
            personality="professional",
            max_tokens=4096,
            temperature=0.7,
        )

        assert config.agent_type == AgentType.CODE
        assert config.language == "en"
        assert config.max_tokens == 4096

    def test_agent_config_defaults(self):
        """Test agent config default values"""
        config = AgentConfig()

        assert config.agent_type == AgentType.GENERAL
        assert config.language == "en"
        assert config.personality == "professional"
        assert config.max_tokens == 4096
        assert config.temperature == 1.0
        assert config.permission_mode == PermissionMode.ASK

    def test_agent_config_model_field(self):
        """Test agent config model field"""
        config = AgentConfig(model="claude-sonnet-4-5-20250929")

        assert config.model == "claude-sonnet-4-5-20250929"

    def test_agent_config_working_directory(self):
        """Test agent config working directory"""
        config = AgentConfig(working_directory="/tmp/test-agent")

        assert config.working_directory == "/tmp/test-agent"

    def test_agent_config_environment_vars(self):
        """Test agent config environment variables"""
        env_vars = {"MY_VAR": "value", "ANOTHER_VAR": "another_value"}
        config = AgentConfig(environment=env_vars)

        assert config.environment == env_vars
        assert config.environment["MY_VAR"] == "value"
