#!/usr/bin/env python3
"""
#exonware/xwaction/src/exonware/xwaction/common/workflow_visualizer.py
Workflow Visualization Utilities
Company: eXonware.com
Author: eXonware Backend Team
Email: connect@exonware.com
Version: 0.9.0.14
Generation Date: 15-Nov-2025
"""

from typing import Any
from dataclasses import dataclass
from exonware.xwsystem import get_logger
logger = get_logger(__name__)
@dataclass

class WorkflowNode:
    """Node in workflow visualization."""
    action_name: str
    action_type: str
    status: str
    duration: float | None = None
    dependencies: list[str] = None
    metadata: dict[str, Any] = None
@dataclass

class WorkflowEdge:
    """Edge in workflow visualization."""
    source: str
    target: str
    condition: str | None = None
    metadata: dict[str, Any] = None


class WorkflowVisualizer:
    """Utilities for visualizing workflows."""
    @staticmethod

    def generate_graphviz(
        nodes: list[WorkflowNode],
        edges: list[WorkflowEdge],
        title: str = "Workflow"
    ) -> str:
        """
        Generate Graphviz DOT format for workflow visualization.
        Args:
            nodes: List of workflow nodes
            edges: List of workflow edges
            title: Workflow title
        Returns:
            Graphviz DOT format string
        """
        lines = [
            f'digraph "{title}" {{',
            '  rankdir=LR;',
            '  node [shape=box, style=rounded];',
            ''
        ]
        # Add nodes
        for node in nodes:
            color = {
                'completed': 'green',
                'running': 'blue',
                'failed': 'red',
                'pending': 'gray'
            }.get(node.status, 'black')
            label = f"{node.action_name}\\n{node.action_type}"
            if node.duration:
                label += f"\\n{duration:.2f}s"
            lines.append(
                f'  "{node.action_name}" [label="{label}", color={color}];'
            )
        lines.append('')
        # Add edges
        for edge in edges:
            attrs = []
            if edge.condition:
                attrs.append(f'label="{edge.condition}"')
            if edge.metadata:
                for k, v in edge.metadata.items():
                    attrs.append(f'{k}="{v}"')
            attr_str = f' [{", ".join(attrs)}]' if attrs else ''
            lines.append(f'  "{edge.source}" -> "{edge.target}"{attr_str};')
        lines.append('}')
        return '\n'.join(lines)
    @staticmethod

    def generate_mermaid(
        nodes: list[WorkflowNode],
        edges: list[WorkflowEdge],
        title: str = "Workflow"
    ) -> str:
        """
        Generate Mermaid format for workflow visualization.
        Args:
            nodes: List of workflow nodes
            edges: List of workflow edges
            title: Workflow title
        Returns:
            Mermaid format string
        """
        lines = [
            f'graph LR',
            ''
        ]
        # Add nodes
        for node in nodes:
            style = {
                'completed': 'fill:#90EE90',
                'running': 'fill:#87CEEB',
                'failed': 'fill:#FF6B6B',
                'pending': 'fill:#D3D3D3'
            }.get(node.status, '')
            node_id = node.action_name.replace(' ', '_').replace('-', '_')
            label = f"{node.action_name} ({node.action_type})"
            if style:
                lines.append(f'  {node_id}["{label}"]:::completed')
            else:
                lines.append(f'  {node_id}["{label}"]')
        lines.append('')
        # Add edges
        for edge in edges:
            source_id = edge.source.replace(' ', '_').replace('-', '_')
            target_id = edge.target.replace(' ', '_').replace('-', '_')
            if edge.condition:
                lines.append(f'  {source_id} -->|"{edge.condition}"| {target_id}')
            else:
                lines.append(f'  {source_id} --> {target_id}')
        return '\n'.join(lines)
    @staticmethod

    def generate_json(
        nodes: list[WorkflowNode],
        edges: list[WorkflowEdge],
        metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Generate JSON representation of workflow.
        Args:
            nodes: List of workflow nodes
            edges: List of workflow edges
            metadata: Optional workflow metadata
        Returns:
            Dictionary with workflow representation
        """
        return {
            'metadata': metadata or {},
            'nodes': [
                {
                    'name': node.action_name,
                    'type': node.action_type,
                    'status': node.status,
                    'duration': node.duration,
                    'dependencies': node.dependencies or [],
                    'metadata': node.metadata or {}
                }
                for node in nodes
            ],
            'edges': [
                {
                    'source': edge.source,
                    'target': edge.target,
                    'condition': edge.condition,
                    'metadata': edge.metadata or {}
                }
                for edge in edges
            ]
        }
