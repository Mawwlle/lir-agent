# lir-agent

![License](https://img.shields.io/github/license/Mawwlle/lir-agent?style=flat&logo=opensourceinitiative&logoColor=white&color=blue)
[![OSA-improved](https://img.shields.io/badge/improved%20by-OSA-yellow)](https://github.com/aimclub/OSA)

## Overview

This project provides an intelligent agent capable of dynamically expanding its own abilities by creating and using new tools as needed. It helps users solve problems by reasoning, acting, and adapting its functionalities in real-time, offering a flexible and self-improving problem-solving assistant.

## Demo
https://github.com/user-attachments/assets/79a93a52-9944-463d-b7e8-41e13ed04579


## Table of Contents

- [Core features](#core-features)
- [Installation](#installation)
- [Contributing](#contributing)
- [License](#license)
- [Citation](#citation)

## Core features

1.  **Runtime Tool Creation**: The agent can dynamically create new Python tools at runtime by generating Python code, saving it to a file, importing it as a module, and registering its entrypoint function for later use. This allows the agent to adapt and extend its capabilities on the fly.
2.  **Dynamic Tool Execution**: The agent can execute any registered tool dynamically by its name, passing arguments as needed. This enables the agent to utilize both pre-defined and newly created tools seamlessly within its workflow.
3.  **Dependency Management**: The agent includes a tool to install Python packages within its virtual environment. This ensures that any new tools created or used by the agent can have their necessary dependencies met without manual intervention.
4.  **ReAct Agent Loop**: The agent operates based on a ReAct (Reasoning and Acting) loop, where it follows a Thought → Action → Observation sequence. This structured approach guides the agent in problem-solving, tool creation, and tool usage.
5.  **LLM Integration (LangChain)**: The agent leverages LangChain for integrating with Large Language Models (LLMs), specifically ChatOpenAI. This allows the agent to understand natural language prompts, reason about tasks, and generate appropriate actions, including tool creation and usage.

## Installation

**Prerequisites:** requires Python >=3.12

Install lir-agent using one of the following methods:

**Build from source:**

1.  Clone the lir-agent repository:

    ```sh
    git clone https://github.com/Mawwlle/lir-agent
    ```

2.  Navigate to the project directory:

    ```sh
    cd lir-agent
    ```

3.  Install the project dependencies:

    ```sh
    pip install -r requirements.txt
    ```

## Contributing

-   **[Report Issues](https://github.com/Mawwlle/lir-agent/issues)**: Submit bugs found or log feature requests for the project.

## License

This project is protected under the MIT License. For more details, refer to the [LICENSE](https://github.com/Mawwlle/lir-agent/tree/master/LICENSE) file.

## Citation

If you use this software, please cite it as below.

### APA format:

    Mawwlle (2026). lir-agent repository [Computer software]. https://github.com/Mawwlle/lir-agent

### BibTeX format:

    @misc{lir-agent,
        author = {Mawwlle},
        title = {lir-agent repository},
        year = {2026},
        publisher = {github.com},
        journal = {github.com repository},
        howpublished = {\url{https://github.com/Mawwlle/lir-agent.git}},
        url = {https://github.com/Mawwlle/lir-agent.git}
    }
