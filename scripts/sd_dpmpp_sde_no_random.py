from modules import scripts
from modules import script_callbacks
from modules.processing import Processed, process_images
from modules.shared import opts, OptionInfo
import torch
import k_diffusion.sampling

def create_hijacked_init(literal_seed):
    def BrownianTreeNoiseSampler_init(self, x, sigma_min, sigma_max, seed=None, transform=lambda x: x):
        self.transform = transform
        t0, t1 = self.transform(torch.as_tensor(sigma_min)), self.transform(torch.as_tensor(sigma_max))
        self.tree = k_diffusion.sampling.BatchedBrownianTree(x, t0, t1, seed=int(float("{}".format(literal_seed))))
    return BrownianTreeNoiseSampler_init

class Script(scripts.Script):
    def title(self):
        return "Prevent DPM++ SDE Karras from always using a random seed"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def process(self, p):
        if opts.sd_dpmpp_sde_no_random:
            # Save the original "BrownianTreeNoiseSampler.__init__"
            p.orig_BrownianTreeNoiseSampler_init = k_diffusion.sampling.BrownianTreeNoiseSampler.__init__
            # Create a hijacked version with the current seed as a literal and assign it to BrownianTreeNoiseSampler.__init__
            BrownianTreeNoiseSampler_init = create_hijacked_init(p.all_seeds[0])
            k_diffusion.sampling.BrownianTreeNoiseSampler.__init__ = BrownianTreeNoiseSampler_init

    def postprocess(self, p, processed):
        if opts.sd_dpmpp_sde_no_random:
            # Restore the original "BrownianTreeNoiseSampler.__init__"
            k_diffusion.sampling.BrownianTreeNoiseSampler.__init__ = p.orig_BrownianTreeNoiseSampler_init

# Add option to settings
def on_ui_settings():
    opts.add_option("sd_dpmpp_sde_no_random", OptionInfo(False, "Prevent DPM++ SDE Karras from always using a random seed", section=("sampler-params", "Sampler parameters")))

script_callbacks.on_ui_settings(on_ui_settings)
            