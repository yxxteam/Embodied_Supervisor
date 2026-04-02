from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from data.models import ArmCommandPacket

from api.deps import RepositoryBundle, get_repositories
from api.guidance.service import build_arm_command_packet
from api.schemas import RobotParameterInputRequest


router = APIRouter(tags=["guidance"])


@router.post("/sessions/{session_id}/robot-parameter-inputs", response_model=ArmCommandPacket, status_code=status.HTTP_201_CREATED)
def create_robot_parameter_packet(
    session_id: str,
    payload: RobotParameterInputRequest,
    repositories: RepositoryBundle = Depends(get_repositories),
) -> ArmCommandPacket:
    session = repositories.session_repo.get(session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session_not_found")
    packet = build_arm_command_packet(session, payload)
    return repositories.robot_command_repo.create(packet)


@router.get("/sessions/{session_id}/robot-parameter-inputs/latest", response_model=ArmCommandPacket)
def get_latest_robot_parameter_packet(
    session_id: str,
    repositories: RepositoryBundle = Depends(get_repositories),
) -> ArmCommandPacket:
    session = repositories.session_repo.get(session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session_not_found")
    packet = repositories.robot_command_repo.get_latest(session_id)
    if packet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="robot_parameter_packet_not_found")
    return packet
