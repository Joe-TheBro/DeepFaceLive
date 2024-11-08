from pathlib import Path
from apps.DeepFaceLive import backend
from apps.DeepFaceLive.backend import (
    BackendDB,
    BackendWeakHeap,
    BackendSignal,
    # FileSource,
    CameraSource,
    FaceDetector,
    FaceMarker,
    FaceAligner,
    # FaceAnimator,
    FaceSwapInsight,
    # FaceSwapDFM,
    FrameAdjuster,
    FaceMerger,
    StreamOutput,
)

# Define paths
userdata_path = Path("../data")
settings_dirpath = userdata_path / "settings"
settings_dirpath.mkdir(parents=True, exist_ok=True)

backend_db = BackendDB(settings_dirpath / "states.dat")
backend_weak_heap = BackendWeakHeap(size_mb=2048)
reemit_frame_signal = BackendSignal()

multi_sources_bc_out = backend.BackendConnection(multi_producer=True)
face_detector_bc_out = backend.BackendConnection()
face_marker_bc_out = backend.BackendConnection()
face_aligner_bc_out = backend.BackendConnection()
face_swapper_bc_out = backend.BackendConnection()
frame_adjuster_bc_out = backend.BackendConnection()
face_merger_bc_out = backend.BackendConnection()

# file_source = FileSource(
#     weak_heap=backend_weak_heap,
#     reemit_frame_signal=reemit_frame_signal,
#     bc_out=multi_sources_bc_out,
#     backend_db=backend_db,
# )

camera_source = CameraSource(
    weak_heap=backend_weak_heap, bc_out=multi_sources_bc_out, backend_db=backend_db
)
camera_sheet_control = camera_source.get_control_sheet()
camera_sheet_control.resolution.select(6) # 1080p
camera_sheet_control.drivers.select(0) # compatible driver
camera_sheet_control.device_idx.select(0) # first camera

face_detector = FaceDetector(
    weak_heap=backend_weak_heap,
    reemit_frame_signal=reemit_frame_signal,
    bc_in=multi_sources_bc_out,
    bc_out=face_detector_bc_out,
    backend_db=backend_db,
)
face_detector_sheet_control = face_detector.get_control_sheet()
face_detector_sheet_control.detector_type.select(2) # YoloV5
face_detector_sheet_control.sort_by.select(1) # dist from center

face_marker = FaceMarker(
    weak_heap=backend_weak_heap,
    reemit_frame_signal=reemit_frame_signal,
    bc_in=face_detector_bc_out,
    bc_out=face_marker_bc_out,
    backend_db=backend_db,
)
face_marker_sheet_control = face_marker.get_control_sheet()
face_marker_sheet_control.marker_type.select(1) # google facemesh

face_aligner = FaceAligner(
    weak_heap=backend_weak_heap,
    reemit_frame_signal=reemit_frame_signal,
    bc_in=face_marker_bc_out,
    bc_out=face_aligner_bc_out,
    backend_db=backend_db,
)
face_aligner_sheet_control = face_aligner.get_control_sheet()
face_aligner_sheet_control.align_mode.select(1) # from points

# face_animator = FaceAnimator(
#     weak_heap=backend_weak_heap,
#     reemit_frame_signal=reemit_frame_signal,
#     bc_in=face_aligner_bc_out,
#     bc_out=face_merger_bc_out,
#     backend_db=backend_db,
# )

face_swap_insight = FaceSwapInsight(
    faces_path=userdata_path,
    weak_heap=backend_weak_heap,
    reemit_frame_signal=reemit_frame_signal,
    bc_in=face_aligner_bc_out,
    bc_out=face_swapper_bc_out,
    backend_db=backend_db,
)
face_swap_insight_sheet_control = face_swap_insight.get_control_sheet()
face_swap_insight_sheet_control.face.select(0) # first face

# face_swap_dfm = FaceSwapDFM(
    # weak_heap=backend_weak_heap,
    # reemit_frame_signal=reemit_frame_signal,
    # bc_in=face_aligner_bc_out,
    # bc_out=face_swapper_bc_out,
    # backend_db=backend_db,
# )

frame_adjuster = FrameAdjuster(
    weak_heap=backend_weak_heap,
    reemit_frame_signal=reemit_frame_signal,
    bc_in=face_swapper_bc_out,
    bc_out=frame_adjuster_bc_out,
    backend_db=backend_db,
)
# frame_adjuster_sheet_control = frame_adjuster.get_control_sheet()

face_merger = FaceMerger(
    weak_heap=backend_weak_heap,
    reemit_frame_signal=reemit_frame_signal,
    bc_in=frame_adjuster_bc_out,
    bc_out=face_merger_bc_out,
    backend_db=backend_db,
)

stream_output = StreamOutput(
    weak_heap=backend_weak_heap,
    reemit_frame_signal=reemit_frame_signal,
    bc_in=face_merger_bc_out,
    backend_db=backend_db,
)
stream_output_sheet_control = stream_output.get_control_sheet()
stream_output_sheet_control.source_type.select(3) # merged face
stream_output_sheet_control.is_streaming.set_flag(True) # start streaming

all_backends = [
    # file_source,
    camera_source,
    face_detector,
    face_marker,
    face_aligner,
    # face_animator,
    face_swap_insight,
    # face_swap_dfm,
    frame_adjuster,
    face_merger,
    stream_output,
]

for backend in all_backends:
    backend.start()
       
while True:
    for backend in all_backends:
        backend.process_messages()