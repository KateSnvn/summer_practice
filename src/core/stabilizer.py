import numpy as np
import cv2
from PIL import Image


def pil_to_cv2(image):
    arr = np.array(image)
    if len(arr.shape) == 3 and arr.shape[2] == 4:
        arr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
    elif len(arr.shape) == 3 and arr.shape[2] == 3:
        arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    else:
        arr = cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)
    return arr


def cv2_to_pil(image):
    arr = cv2.cvtColor(image, cv2.COLOR_BGR2RGBA)
    return Image.fromarray(arr)


def stabilize_ecc(frames, smoothing=0.5):
    if len(frames) < 2:
        return frames

    cv_frames = [pil_to_cv2(f) for f in frames]
    gray_frames = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in cv_frames]

    ref_gray = gray_frames[0]
    h, w = ref_gray.shape
    warp_matrix = np.eye(2, 3, dtype=np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 50, 1e-5)

    stabilized = [frames[0]]

    for i in range(1, len(cv_frames)):
        try:
            _, warp_matrix = cv2.findTransformECC(
                ref_gray, gray_frames[i], warp_matrix,
                cv2.MOTION_AFFINE, criteria
            )
            h_mat = np.vstack([warp_matrix, [0, 0, 1]])

            smoothed = np.eye(3, dtype=np.float32) * (1 - smoothing) + h_mat * smoothing
            smoothed_affine = smoothed[:2, :]

            stabilized_frame = cv2.warpAffine(
                cv_frames[i], smoothed_affine, (w, h),
                flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP,
                borderMode=cv2.BORDER_REPLICATE
            )
            stabilized.append(cv2_to_pil(stabilized_frame))
        except Exception:
            stabilized.append(frames[i])

    return stabilized


def stabilize_orb(frames, smoothing=0.5):
    if len(frames) < 2:
        return frames

    cv_frames = [pil_to_cv2(f) for f in frames]
    gray_frames = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in cv_frames]

    orb = cv2.ORB_create(nfeatures=2000)
    ref_gray = gray_frames[0]
    ref_kp, ref_des = orb.detectAndCompute(ref_gray, None)
    h, w = ref_gray.shape
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    stabilized = [frames[0]]

    for i in range(1, len(cv_frames)):
        try:
            kp, des = orb.detectAndCompute(gray_frames[i], None)
            if des is None or ref_des is None or len(kp) < 4:
                stabilized.append(frames[i])
                continue

            matches = bf.match(ref_des, des)
            matches = sorted(matches, key=lambda x: x.distance)[:100]

            if len(matches) < 4:
                stabilized.append(frames[i])
                continue

            ref_pts = np.float32([ref_kp[m.queryIdx].pt for m in matches])
            cur_pts = np.float32([kp[m.trainIdx].pt for m in matches])

            mat, _ = cv2.estimateAffinePartial2D(cur_pts, ref_pts, method=cv2.RANSAC)
            if mat is None:
                stabilized.append(frames[i])
                continue

            h_mat = np.vstack([mat, [0, 0, 1]])
            smoothed = np.eye(3, dtype=np.float32) * (1 - smoothing) + h_mat * smoothing
            smoothed_affine = smoothed[:2, :]

            stabilized_frame = cv2.warpAffine(
                cv_frames[i], smoothed_affine, (w, h),
                flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP,
                borderMode=cv2.BORDER_REPLICATE
            )
            stabilized.append(cv2_to_pil(stabilized_frame))
        except Exception:
            stabilized.append(frames[i])

    return stabilized


def stabilize_sift(frames, smoothing=0.5):
    if len(frames) < 2:
        return frames

    cv_frames = [pil_to_cv2(f) for f in frames]
    gray_frames = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in cv_frames]

    sift = cv2.SIFT_create(nfeatures=2000)
    ref_gray = gray_frames[0]
    ref_kp, ref_des = sift.detectAndCompute(ref_gray, None)
    h, w = ref_gray.shape

    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)

    stabilized = [frames[0]]

    for i in range(1, len(cv_frames)):
        try:
            kp, des = sift.detectAndCompute(gray_frames[i], None)
            if des is None or ref_des is None or len(kp) < 2:
                stabilized.append(frames[i])
                continue

            matches = flann.knnMatch(ref_des, des, k=2)

            good = []
            for pair in matches:
                if len(pair) == 2:
                    m, n = pair
                    if m.distance < 0.75 * n.distance:
                        good.append(m)

            if len(good) < 4:
                stabilized.append(frames[i])
                continue

            ref_pts = np.float32([ref_kp[m.queryIdx].pt for m in good])
            cur_pts = np.float32([kp[m.trainIdx].pt for m in good])

            mat, _ = cv2.estimateAffinePartial2D(cur_pts, ref_pts, method=cv2.RANSAC)
            if mat is None:
                stabilized.append(frames[i])
                continue

            h_mat = np.vstack([mat, [0, 0, 1]])
            smoothed = np.eye(3, dtype=np.float32) * (1 - smoothing) + h_mat * smoothing
            smoothed_affine = smoothed[:2, :]

            stabilized_frame = cv2.warpAffine(
                cv_frames[i], smoothed_affine, (w, h),
                flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP,
                borderMode=cv2.BORDER_REPLICATE
            )
            stabilized.append(cv2_to_pil(stabilized_frame))
        except Exception:
            stabilized.append(frames[i])

    return stabilized


def stabilize_frames(frames, algorithm="ECC", smoothing=0.5):
    if algorithm == "ECC":
        return stabilize_ecc(frames, smoothing)
    elif algorithm == "ORB":
        return stabilize_orb(frames, smoothing)
    elif algorithm == "SIFT":
        return stabilize_sift(frames, smoothing)
    else:
        return frames
