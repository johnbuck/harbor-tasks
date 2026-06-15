"""Offline unit checks for ExternalAgentAdapter.run (lib.external_agent).

Encodes spec success criterion #4: run() captures the response correctly for
response=stdout, response=file:<path>, and response=json:<jsonpath>, templates
{instruction} shell-quoted into the invoke command, and writes the captured
transcript to logs_dir/external.txt on the host.

The agent environment is mocked at the boundary (FakeEnvironment); the adapter's
render + capture + transcript-write logic runs for real.
"""
import shlex

from harbor.models.agent.context import AgentContext

from prod_agent_support import FakeEnvironment, make_agent_adapter, run_async


def test_response_stdout_is_captured_to_external_txt(tmp_path):
    fe = FakeEnvironment()
    fe.exec_stdout = "STDOUT_ANSWER_TOKEN"
    adapter = make_agent_adapter(
        tmp_path, invoke="myagent --message {instruction}", response="stdout"
    )

    run_async(adapter.run("hello world", fe, AgentContext()))

    transcript = (tmp_path / "external.txt").read_text()
    assert "STDOUT_ANSWER_TOKEN" in transcript


def test_instruction_is_shell_quoted_into_invoke(tmp_path):
    fe = FakeEnvironment()
    fe.exec_stdout = "ok"
    adapter = make_agent_adapter(
        tmp_path, invoke="myagent --message {instruction}", response="stdout"
    )

    nasty = "what's up? $HOME && rm -rf /"
    run_async(adapter.run(nasty, fe, AgentContext()))

    assert fe.exec_calls, "adapter never exec'd the invoke command"
    command = fe.exec_calls[0]["command"]
    assert shlex.quote(nasty) in command, (
        "the instruction must be shell-quoted when templated into invoke"
    )


def test_response_file_is_downloaded_and_captured(tmp_path):
    fe = FakeEnvironment()
    fe.download_payload = "FILE_ANSWER_TOKEN"
    adapter = make_agent_adapter(
        tmp_path,
        invoke="myagent run --out /out/answer.txt --message {instruction}",
        response="file:/out/answer.txt",
    )

    run_async(adapter.run("question", fe, AgentContext()))

    assert any(src == "/out/answer.txt" for src, _ in fe.downloaded), (
        "file response mode must download the configured path from the container"
    )
    transcript = (tmp_path / "external.txt").read_text()
    assert "FILE_ANSWER_TOKEN" in transcript


def test_response_json_path_is_extracted_and_captured(tmp_path):
    fe = FakeEnvironment()
    fe.exec_stdout = '{"result": {"answer": "JSON_ANSWER_TOKEN"}, "noise": 1}'
    adapter = make_agent_adapter(
        tmp_path,
        invoke="myagent chat --json --message {instruction}",
        response="json:result.answer",
    )

    run_async(adapter.run("question", fe, AgentContext()))

    transcript = (tmp_path / "external.txt").read_text()
    assert "JSON_ANSWER_TOKEN" in transcript
    # Must extract the addressed field, not dump the whole JSON blob.
    assert '"noise"' not in transcript
